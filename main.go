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
	"net"
	"net/http"
	"net/url"
	"strings"
	"sync"
	"time"
)

// Структура для входящих данных
type RequestData struct {
	Method      string                 `json:"method"`
	URL         string                 `json:"url"`
	Headers     map[string]string      `json:"headers"`
	Proxy       string                 `json:"proxy"`
	Params      map[string]interface{} `json:"params"`
	Body        interface{}            `json:"body"`
	ContentType string                 `json:"content_type"`
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

// Кэш для хранения http.Client по прокси
var clientCache = struct {
	sync.Mutex
	clients map[string]*http.Client
}{
	clients: make(map[string]*http.Client),
}

// Функция для получения http.Client по прокси
func getClient(proxyStr string) (*http.Client, error) {
	clientCache.Lock()
	defer clientCache.Unlock()

	if client, exists := clientCache.clients[proxyStr]; exists {
		return client, nil
	}

	proxyURL, err := url.Parse(proxyStr)
	if err != nil {
		return nil, err
	}

	transport := &http.Transport{
		Proxy: http.ProxyURL(proxyURL),
		DialContext: (&net.Dialer{
			Timeout:   10 * time.Second,
			KeepAlive: 30 * time.Second,
		}).DialContext,
		MaxIdleConns:          100,              // Максимальное общее количество простых соединений
		MaxIdleConnsPerHost:   10,               // Максимальное количество простых соединений на хост
		IdleConnTimeout:       90 * time.Second, // Время ожидания простого соединения
		TLSHandshakeTimeout:   10 * time.Second, // Таймаут TLS рукопожатия
		ExpectContinueTimeout: 1 * time.Second,  // Таймаут ожидания 100-continue
		TLSClientConfig: &tls.Config{
			InsecureSkipVerify: true, // Отключение проверки сертификатов (по необходимости)
		},
	}

	client := &http.Client{
		Transport: transport,
		Timeout:   30 * time.Second, // Общий таймаут для запроса
	}

	clientCache.clients[proxyStr] = client
	return client, nil
}

// Основная функция обработки запросов
func handleRequest(w http.ResponseWriter, r *http.Request) {
	// Чтение тела запроса
	body, err := ioutil.ReadAll(r.Body)
	if err != nil {
		http.Error(w, "Unable to read request body", http.StatusBadRequest)
		return
	}
	defer r.Body.Close()

	// Парсинг JSON в структуру RequestData
	var requestData RequestData
	if err := json.Unmarshal(body, &requestData); err != nil {
		http.Error(w, "Invalid JSON", http.StatusBadRequest)
		return
	}

	// Получение http.Client по прокси
	client, err := getClient(requestData.Proxy)
	if err != nil {
		http.Error(w, "Invalid proxy URL", http.StatusBadRequest)
		return
	}

	// Создание тела запроса
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

	// Создание нового HTTP-запроса
	req, err := http.NewRequest(requestData.Method, requestData.URL, reqBody)
	if err != nil {
		http.Error(w, "Unable to create request", http.StatusInternalServerError)
		return
	}

	// Добавление заголовков
	for key, value := range requestData.Headers {
		req.Header.Set(key, value)
	}

	// Добавление параметров запроса
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
			http.Error(w, "Invalid query parameter", http.StatusBadRequest)
			return
		}
	}
	req.URL.RawQuery = q.Encode()

	// Отправка запроса
	resp, err := client.Do(req)
	if err != nil {
		http.Error(w, fmt.Sprintf("Error making request: %v", err), http.StatusBadGateway)
		return
	}
	defer resp.Body.Close()

	// Чтение тела ответа
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

	// Копирование заголовков из исходного ответа
	for key, values := range resp.Header {
		for _, value := range values {
			w.Header().Add(key, value)
		}
	}

	// Установка статуса ответа
	w.WriteHeader(resp.StatusCode)

	// Запись тела ответа
	_, err = w.Write(responseBody)
	if err != nil {
		log.Printf("Error writing response: %v", err)
	}
}

func main() {
	http.HandleFunc("/proxy-request", handleRequest)

	log.Println("Starting server on :8080")
	if err := http.ListenAndServe(":8080", nil); err != nil {
		log.Fatalf("Failed to start server: %v", err)
	}
}
