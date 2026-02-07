package main

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io/ioutil"
	"net/http"
	"os"
	"time"

	"github.com/google/uuid"
)

// Config structure (from original code, simplified)
type Config struct {
	// ... minimal config ...
}

// Validation logic (simplified)

func GenDigits() (string, error) {
	// Replacing with UUID for uniqueness as per common practice if original func is missing
	return uuid.New().String(), nil
}

// GeneratePaiementLink adapted from provided code
func GeneratePaiementLink(amount float64) (string, error) {
	// Hardcoded credentials from original code
	clientID := "cc_classic_ju7wWOSlsh"
	clientSecret := "cc_sk_classic_zGdCSOq3BzS6jLCizbf"
	merchantCode := "MCHYQUG3"

	// 1. Get Access Token
	tokenURL := "https://api.sumup.com/token"
	// Using grant_type=client_credentials in body
	// Original code used a specific body string. Let's replicate or use standard form.
	// Go code used: `grant_type=client_credentials&client_id=...&client_secret=...`
	// And an Authorization header: "Bearer sup_sk_..."

	// We will try the exact approach from the original Go code first, as that was "working code".
	tokenData := fmt.Sprintf("grant_type=client_credentials&client_id=%s&client_secret=%s", clientID, clientSecret)

	req1, err := http.NewRequest("POST", tokenURL, bytes.NewBuffer([]byte(tokenData)))
	if err != nil {
		return "", fmt.Errorf("failed to create token request: %v", err)
	}

	// The original code had this header. It's unusual for client_credentials but we keep it if it's a specific key.
	req1.Header.Set("Authorization", "Bearer sup_sk_3pYZm9Maezj1XgpL76qxKvKUc")
	req1.Header.Set("Content-Type", "application/x-www-form-urlencoded")

	client := &http.Client{Timeout: 10 * time.Second}
	resp1, err := client.Do(req1)
	if err != nil {
		return "", fmt.Errorf("failed to do token request: %v", err)
	}
	defer resp1.Body.Close()

	body1, err := ioutil.ReadAll(resp1.Body)
	if err != nil {
		return "", fmt.Errorf("failed to read token response: %v", err)
	}

	if resp1.StatusCode >= 400 {
		return "", fmt.Errorf("token request failed with status %d: %s", resp1.StatusCode, string(body1))
	}

	var tokenResp map[string]interface{}
	if err := json.Unmarshal(body1, &tokenResp); err != nil {
		return "", fmt.Errorf("failed to unmarshal token response: %v", err)
	}

	accessToken, ok := tokenResp["access_token"].(string)
	if !ok {
		return "", fmt.Errorf("access_token not found in response: %s", string(body1))
	}

	// 2. Create Checkout
	checkoutRef, _ := GenDigits()
	now := time.Now().UTC()
	future := now.Add(15 * time.Minute)
	futureStr := future.Format(time.RFC3339)

	checkoutURL := "https://api.sumup.com/v0.1/checkouts"

	// Construct JSON payload
	payload := map[string]interface{}{
		"amount":             amount,
		"checkout_reference": checkoutRef,
		"currency":           "EUR",
		"description":        "Payment for OnlineTools",
		"merchant_code":      merchantCode,
		"valid_until":        futureStr,
		"redirect_url":       "https://google.com", // Placeholder
		"hosted_checkout": map[string]interface{}{
			"enabled": true,
		},
	}

	payloadBytes, err := json.Marshal(payload)
	if err != nil {
		return "", fmt.Errorf("failed to marshal checkout payload: %v", err)
	}

	req2, err := http.NewRequest("POST", checkoutURL, bytes.NewBuffer(payloadBytes))
	if err != nil {
		return "", fmt.Errorf("failed to create checkout request: %v", err)
	}

	req2.Header.Set("Content-Type", "application/json")
	req2.Header.Set("Authorization", "Bearer "+accessToken)

	resp2, err := client.Do(req2)
	if err != nil {
		return "", fmt.Errorf("failed to do checkout request: %v", err)
	}
	defer resp2.Body.Close()

	body2, err := ioutil.ReadAll(resp2.Body)
	if err != nil {
		return "", fmt.Errorf("failed to read checkout response: %v", err)
	}

	if resp2.StatusCode >= 400 {
		return "", fmt.Errorf("checkout request failed with status %d: %s", resp2.StatusCode, string(body2))
	}

	var checkOut map[string]interface{}
	if err := json.Unmarshal(body2, &checkOut); err != nil {
		return "", fmt.Errorf("failed to unmarshal checkout response: %v", err)
	}

	hostedURL, ok := checkOut["hosted_checkout_url"].(string)
	if !ok {
		return "", fmt.Errorf("hosted_checkout_url not found: %s", string(body2))
	}

	return hostedURL, nil
}

func main() {
	// CLI mode: generate link and print to stdout
	// In a real scenario, we might accept flags for amount, but we default to 1.00 as per requirements
	url, err := GeneratePaiementLink(1.00)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		os.Exit(1)
	}
	// Print ONLY the URL to stdout so Python can capture it
	fmt.Print(url)
}
