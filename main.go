package main

import (
	"bytes"
	"compress/gzip"
	"crypto/tls"
	"encoding/json"
	"fmt"
	"io"
	"io/ioutil"
	"log"
	"net/http"
	"net/url"
	"strings"
	"sync"
	"time"
)

// Структура для входящих данных
type RequestData struct {
	Method      string            `json:"method"`
	URL         string            `json:"url"`
	Headers     map[string]string `json:"headers"`
	Proxy       string            `json:"proxy"`
	Params      map[string]string `json:"params"`
	Body        interface{}       `json:"body"`         // Может содержать либо JSON, либо данные формы
	ContentType string            `json:"content_type"` // Указывает, является ли тело JSON или form data
}

// Функция для распаковки GZIP с потоковым чтением
func decompressGZIPStream(reader io.Reader) ([]byte, error) {
	gzipReader, err := gzip.NewReader(reader)
	if err != nil {
		return nil, err
	}
	defer gzipReader.Close()

	return ioutil.ReadAll(gzipReader)
}

// Оптимизированный обработчик запросов
func handleRequest(w http.ResponseWriter, r *http.Request) {
	// Чтение тела запроса
	body, err := ioutil.ReadAll(r.Body)
	if err != nil {
		http.Error(w, "Unable to read request body", http.StatusBadRequest)
		return
	}

	// Парсинг JSON в структуру RequestData
	var requestData RequestData
	err = json.Unmarshal(body, &requestData)
	if err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	// Преобразование прокси-строки в *url.URL
	proxyURL, err := url.Parse(requestData.Proxy)
	if err != nil {
		http.Error(w, "Invalid proxy URL", http.StatusBadRequest)
		return
	}

	// Получение HTTP-клиента из пула
	client := getClient(proxyURL)

	// Создание тела запроса в зависимости от типа данных
	var reqBody io.Reader
	if requestData.Body != nil {
		if requestData.ContentType == "application/json" {
			jsonData, err := json.Marshal(requestData.Body)
			if err != nil {
				http.Error(w, "Failed to encode JSON body", http.StatusInternalServerError)
				return
			}
			reqBody = bytes.NewBuffer(jsonData)
		} else if requestData.ContentType == "application/x-www-form-urlencoded" {
			formData := url.Values{}
			for key, value := range requestData.Body.(map[string]string) {
				formData.Set(key, value)
			}
			reqBody = strings.NewReader(formData.Encode())
		} else {
			http.Error(w, "Unsupported content type", http.StatusBadRequest)
			return
		}
	}

	// Создание запроса
	req, err := http.NewRequest(requestData.Method, requestData.URL, reqBody)
	if err != nil {
		http.Error(w, "Unable to create request", http.StatusInternalServerError)
		return
	}

	// Добавление заголовков
	for key, value := range requestData.Headers {
		req.Header.Set(key, value)
	}
	if requestData.ContentType != "" {
		req.Header.Set("Content-Type", requestData.ContentType)
	}

	// Добавление параметров к URL
	q := req.URL.Query()
	for key, value := range requestData.Params {
		q.Add(key, value)
	}
	req.URL.RawQuery = q.Encode()

	// Отправка запроса и получение ответа
	resp, err := client.Do(req)
	if err != nil {
		http.Error(w, fmt.Sprintf("Error making request: %v", err), http.StatusInternalServerError)
		return
	}
	defer resp.Body.Close()

	// Обработка ответа
	var responseBody []byte
	if resp.Header.Get("Content-Encoding") == "gzip" {
		responseBody, err = decompressGZIPStream(resp.Body)
		if err != nil {
			http.Error(w, "Failed to decompress response", http.StatusInternalServerError)
			return
		}
	} else {
		responseBody, err = ioutil.ReadAll(resp.Body)
		if err != nil {
			http.Error(w, "Unable to read response body", http.StatusInternalServerError)
			return
		}
	}

	// Отправка тела ответа обратно клиенту
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(resp.StatusCode)
	w.Write(responseBody)
}

// Пул HTTP-клиентов
var clientPool = sync.Pool{
	New: func() interface{} {
		return &http.Client{
			Timeout: 10 * time.Second,
			Transport: &http.Transport{
				TLSClientConfig: &tls.Config{
					InsecureSkipVerify: true, // Отключение проверки сертификатов (по необходимости)
				},
			},
		}
	},
}

// Получение клиента из пула или создание нового
func getClient(proxyURL *url.URL) *http.Client {
	client := clientPool.Get().(*http.Client)
	client.Transport.(*http.Transport).Proxy = http.ProxyURL(proxyURL)
	return client
}

// Возврат клиента в пул
func putClient(client *http.Client) {
	clientPool.Put(client)
}

func main() {
	// Настройка маршрута
	http.HandleFunc("/proxy-request", func(w http.ResponseWriter, r *http.Request) {
		handleRequest(w, r)
	})

	// Запуск сервера на порту 8080
	log.Println("Starting server on :8080")
	if err := http.ListenAndServe(":8080", nil); err != nil {
		log.Fatalf("Failed to start server: %v", err)
	}
}
