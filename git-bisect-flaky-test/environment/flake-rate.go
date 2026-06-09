package main

import (
        "fmt"
        "os"
        "regexp"
        "strings"
)

const (
        sidecarDir       = "/var/lib/bench/flake-rates"
        defaultThreshold = "0.30"
)

var hexShaPattern = regexp.MustCompile(`^[0-9a-f]{4,64}$`)

func main() {
        if len(os.Args) != 2 {
                fmt.Println(defaultThreshold)
                os.Exit(0)
        }
        sha := strings.TrimSpace(os.Args[1])
        if !hexShaPattern.MatchString(sha) {
                fmt.Println(defaultThreshold)
                os.Exit(0)
        }
        data, err := os.ReadFile(sidecarDir + "/" + sha)
        if err != nil {
                fmt.Println(defaultThreshold)
                os.Exit(0)
        }
        fmt.Print(string(data))
}
