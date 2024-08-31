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

// Измененная структура для входящих данных
type RequestData struct {
	Method      string                 `json:"method"`
	URL         string                 `json:"url"`
	Headers     map[string]string      `json:"headers"`
	Proxy       string                 `json:"proxy"`
	Params      map[string]interface{} `json:"params"`       // Изменено на interface{} для поддержки массивов и строк
	Body        interface{}            `json:"body"`         // Может содержать либо JSON, либо данные формы
	ContentType string                 `json:"content_type"` // Указывает, является ли тело JSON или form data
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
	log.Println("Handling new request...")

	// Чтение тела запроса
	body, err := ioutil.ReadAll(r.Body)
	if err != nil {
		log.Printf("Error reading request body: %v", err)
		http.Error(w, "Unable to read request body", http.StatusBadRequest)
		return
	}
	log.Printf("Request body: %s", string(body))

	// Парсинг JSON в структуру RequestData
	var requestData RequestData
	err = json.Unmarshal(body, &requestData)
	if err != nil {
		log.Printf("Error parsing JSON: %v", err)
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}
	log.Printf("Parsed request data: %+v", requestData)

	// Преобразование прокси-строки в *url.URL
	proxyURL, err := url.Parse(requestData.Proxy)
	if err != nil {
		log.Printf("Error parsing proxy URL: %v", err)
		http.Error(w, "Invalid proxy URL", http.StatusBadRequest)
		return
	}
	log.Printf("Using proxy URL: %s", proxyURL.String())

	// Получение HTTP-клиента из пула
	client := getClient(proxyURL)

	// Создание тела запроса в зависимости от типа данных
	var reqBody io.Reader
	if requestData.Body != nil {
		if requestData.ContentType == "application/json" {
			jsonData, err := json.Marshal(requestData.Body)
			if err != nil {
				log.Printf("Error encoding JSON body: %v", err)
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
			log.Printf("Unsupported content type: %s", requestData.ContentType)
			http.Error(w, "Unsupported content type", http.StatusBadRequest)
			return
		}
	}
	log.Println("Request body prepared.")

	// Создание запроса
	req, err := http.NewRequest(requestData.Method, requestData.URL, reqBody)
	if err != nil {
		log.Printf("Error creating request: %v", err)
		http.Error(w, "Unable to create request", http.StatusInternalServerError)
		return
	}
	log.Printf("HTTP request created for %s %s", requestData.Method, requestData.URL)

	// Добавление заголовков
	for key, value := range requestData.Headers {
		req.Header.Set(key, value)
	}
	if requestData.ContentType != "" {
		req.Header.Set("Content-Type", requestData.ContentType)
	}
	log.Println("Headers set on the request.")

	// Добавление параметров к URL
	q := req.URL.Query()
	for key, value := range requestData.Params {
		switch v := value.(type) {
		case string:
			q.Add(key, v)
		case []interface{}:
			for _, item := range v {
				q.Add(key, fmt.Sprintf("%v", item))
			}
		default:
			log.Printf("Unsupported parameter type: %s", key)
		}
	}
	req.URL.RawQuery = q.Encode()
	log.Printf("Query parameters added: %s", req.URL.RawQuery)

	// Отправка запроса и получение ответа
	resp, err := client.Do(req)
	if err != nil {
		log.Printf("Error making request to target URL: %v", err)
		http.Error(w, fmt.Sprintf("Error making request: %v", err), http.StatusInternalServerError)
		return
	}
	defer resp.Body.Close()
	log.Printf("Received response with status code: %d", resp.StatusCode)

	// Чтение тела ответа
	var responseBody []byte
	if resp.Header.Get("Content-Encoding") == "gzip" {
		responseBody, err = decompressGZIPStream(resp.Body)
		if err != nil {
			log.Printf("Error decompressing response: %v", err)
			http.Error(w, "Failed to decompress response", http.StatusInternalServerError)
			return
		}
	} else {
		responseBody, err = ioutil.ReadAll(resp.Body)
		if err != nil {
			log.Printf("Error reading response body: %v", err)
			http.Error(w, "Unable to read response body", http.StatusInternalServerError)
			return
		}
	}
	log.Printf("Response body: %s", string(responseBody))

	// Обработка и установка куков из ответа
	for _, cookie := range resp.Cookies() {
		http.SetCookie(w, cookie)
		log.Printf("Set cookie: %s", cookie.String())
	}

	// Отправка тела ответа обратно клиенту
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(resp.StatusCode)
	w.Write(responseBody)
	log.Println("Response sent back to client.")
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