package main

import (
	"bufio"
	"bytes"
	"flag"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"os/exec"
	"path/filepath"
	"encoding/json"
	"regexp"
	"runtime"
)

var (
	PRELUDE_API *string
	PRELUDE_CA  *string
	HOSTNAME	*string
)

var re = regexp.MustCompile(`[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}`)

func executable(test string) string {
	bin, _ := os.Executable()
	executable := filepath.Join(filepath.Dir(bin), *PRELUDE_CA, test)

	if runtime.GOOS == "windows" {
		return executable + ".exe"
	} 
	return executable
}

func loop(testID string, dat string) {
	dos := fmt.Sprintf("%s-%s", runtime.GOOS, runtime.GOARCH)

	req, err := http.NewRequest("GET", *PRELUDE_API, nil)
	if err != nil {
		fmt.Println("Verify your API is correct", err)
		return
	}

	req.Header.Set("token", os.Getenv("PRELUDE_TOKEN"))
	req.Header.Set("id", testID)
	req.Header.Set("dos", dos)
	req.Header.Set("dat", dat)
	req.Header.Set("version", "2")

	client := http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		fmt.Println("Failed retreiving test:", err)
		return
	}
	defer resp.Body.Close()

	body, err := io.ReadAll(resp.Body)
	if err != nil {
		fmt.Println("Failed extracting test:", err)
		return
	}

	location := resp.Request.URL.String()
	test := re.FindString(location)

	if test != "" && test == testID {
		parsedURL, _ := url.Parse(location)

		if *PRELUDE_CA == parsedURL.Host {
			executable := executable(test)
			os.WriteFile(executable, body, 0755)
			
			_, err := os.Stat(executable)
			if err == nil {
				cmd := exec.Command(executable)
				cmd.Stdout = os.Stdout
				cmd.Stderr = os.Stderr
				cmd.Run()
	
				if cmd.ProcessState != nil {
					code := cmd.ProcessState.ExitCode()
					loop("", fmt.Sprintf("%s:%d", test, code))
				}
			} else if os.IsNotExist(err) {
				fmt.Println("[P] Test was quarantined (quickly)")
				loop("", fmt.Sprintf("%s:127", test))
			}

		} else {
			fmt.Println("Invalid CA ", parsedURL.Host)
		}
	}
}

func registerEndpoint(accountID string, token string) {
	hostname := *HOSTNAME
	if hostname == "" {
		hostname, _ = os.Hostname()
	}
	jsonData, err := json.Marshal(map[string]string{
		"id": fmt.Sprintf("%s:%s", hostname, "0"),
	})

	req, err := http.NewRequest("POST", fmt.Sprintf("%s/detect/endpoint", *PRELUDE_API), bytes.NewBuffer(jsonData))
	if err != nil {
		fmt.Println("Failed to establish request:", err)
		return
	}
	req.Header.Set("account", accountID)
	req.Header.Set("token", token)
	
	client := &http.Client{}
	resp, err := client.Do(req)
	if err != nil {
		fmt.Println("Error registering endpoint:", err)
		return
	}
	defer resp.Body.Close()
	
	body, err := io.ReadAll(resp.Body)
	if resp.StatusCode == http.StatusOK {
		os.Setenv("PRELUDE_TOKEN", string(body))
		return
	}
	fmt.Println(string(body))
	os.Exit(1)
}

func main() {
	PRELUDE_API = flag.String("api", "https://api.preludesecurity.com", "Detect API")
	PRELUDE_CA = flag.String("ca", "prelude-account-us1-us-east-2.s3.amazonaws.com", "Detect certificate authority")
	HOSTNAME = flag.String("host", "" , "Hostname associated to this probe")

	flag.Parse()
	os.Mkdir(*PRELUDE_CA, 0755)

	var account, token string
	fmt.Print("[P] Enter account ID: ")
	fmt.Scanln(&account)
	fmt.Print("[P] Enter account token: ")
	fmt.Scanln(&token)
	registerEndpoint(account, token)

	fmt.Print("\n\n----- AUTHORIZED AND READY TO RUN TESTS -----\n\n")
	scanner := bufio.NewScanner(os.Stdin)
	
	for {
		fmt.Print("[P] Enter a test ID: ")
		scanner.Scan()
		testID := scanner.Text()
		if testID != "" {
			loop(testID, "")
		}
	}
}