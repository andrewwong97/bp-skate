package main

import (
	"encoding/json"
	"fmt"
	"github.com/gin-gonic/gin"
	"io/ioutil"
	"log"
	"net/http"
	"strconv"
	"strings"
	"time"
)

func getSkateTimes(ctx *gin.Context) {
	// Basic validation, exits early if not authorized
	origin := ctx.GetHeader("token")
	if origin != "Andrew" {
		ctx.Data(http.StatusForbidden, "Forbidden", nil)
		return
	}

	// Query BP API for times
	date := ctx.GetHeader("startDate")
	dateObj, _ := time.Parse("2006-01-02", date)
	res, err := http.Get("https://xola.com/api/experiences/61536b244f19be5b3c6e4241/availability?start=" + date + "&end=" + date + "&privacy=public")
	fmt.Println("Successfully made outbound request")

	// check for response error
	if err != nil {
		log.Fatal(err)
	}

	// read all response body into string and close stream
	data, _ := ioutil.ReadAll(res.Body)
	res.Body.Close()

	// unpack response into { date: { time: count } } map
	skateTimesMap, cleanedMap := map[string]map[string]int{}, map[string]int{}
	json.Unmarshal(data, &skateTimesMap)

	// remove 0 values
	for k, v := range skateTimesMap[date] {
		if v > 0 {
			cleanedMap[k] = v
		}
	}

	var sb strings.Builder
	sb.WriteString("For " + dateObj.Format("Jan 2, 2006") + ":\n")
	for skateTime, count := range cleanedMap {
		timeObj, _ := time.Parse("0304", skateTime)
		sb.WriteString(timeObj.Format("3:04 PM") + " has " + strconv.Itoa(count) + " spots\n")
	}
	fmt.Println("Successfully formatted response")

	ctx.Data(http.StatusOK, "text/plain", []byte(sb.String()))
}

func main() {
	router := gin.Default()
	router.SetTrustedProxies(nil)
	router.GET("/skateTimes", getSkateTimes)

	router.Run("localhost:8080")
}
