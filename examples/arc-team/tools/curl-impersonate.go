package main

import (
	"flag"
	"fmt"
	"io"
	"os"
	"strings"

	http "github.com/bogdanfinn/fhttp"
	tls_client "github.com/bogdanfinn/tls-client"
	"github.com/bogdanfinn/tls-client/profiles"
)

var profileMap = map[string]profiles.ClientProfile{
	"chrome120":  profiles.Chrome_120,
	"chrome124":  profiles.Chrome_124,
	"chrome131":  profiles.Chrome_131,
	"ff117":      profiles.Firefox_117,
	"ff120":      profiles.Firefox_120,
	"ff132":      profiles.Firefox_132,
	"safari15":   profiles.Safari_15_6_1,
	"safari16":   profiles.Safari_16_0,
	"okhttp":     profiles.Okhttp4Android13,
}

func main() {
	profile := flag.String("profile", "chrome131", "TLS profile")
	method := flag.String("method", "GET", "HTTP method")
	data := flag.String("data", "", "Request body")
	silent := flag.Bool("s", false, "Silent mode")
	output := flag.String("o", "", "Output file")
	writeOut := flag.String("w", "", "Write-out format (%{http_code})")
	var headers arrayFlags
	flag.Var(&headers, "H", "Request header (repeatable)")
	flag.Parse()

	if flag.NArg() < 1 {
		fmt.Fprintf(os.Stderr, "Usage: curl-impersonate [options] URL\nProfiles: %s\n", strings.Join(profileNames(), ", "))
		os.Exit(1)
	}
	url := flag.Arg(0)

	clientProfile, ok := profileMap[*profile]
	if !ok {
		fmt.Fprintf(os.Stderr, "Unknown profile: %s\nAvailable: %s\n", *profile, strings.Join(profileNames(), ", "))
		os.Exit(1)
	}

	jar := tls_client.NewCookieJar()
	client, err := tls_client.NewHttpClient(tls_client.NewNoopLogger(),
		tls_client.WithTimeoutSeconds(30),
		tls_client.WithClientProfile(clientProfile),
		tls_client.WithNotFollowRedirects(),
		tls_client.WithCookieJar(jar),
	)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		os.Exit(1)
	}

	var body io.Reader
	if *data != "" {
		body = strings.NewReader(*data)
	}

	req, err := http.NewRequest(strings.ToUpper(*method), url, body)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		os.Exit(1)
	}

	for _, h := range headers {
		parts := strings.SplitN(h, ":", 2)
		if len(parts) == 2 {
			req.Header.Set(strings.TrimSpace(parts[0]), strings.TrimSpace(parts[1]))
		}
	}

	resp, err := client.Do(req)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		os.Exit(1)
	}
	defer resp.Body.Close()

	respBody, _ := io.ReadAll(resp.Body)

	if *writeOut != "" {
		fmt.Print(strings.ReplaceAll(*writeOut, "%{http_code}", fmt.Sprintf("%d", resp.StatusCode)))
		return
	}

	if *output != "" {
		os.WriteFile(*output, respBody, 0644)
	} else if !*silent {
		os.Stdout.Write(respBody)
	}
}

type arrayFlags []string
func (i *arrayFlags) String() string     { return strings.Join(*i, ", ") }
func (i *arrayFlags) Set(v string) error { *i = append(*i, v); return nil }

func profileNames() []string {
	names := make([]string, 0, len(profileMap))
	for k := range profileMap { names = append(names, k) }
	return names
}
