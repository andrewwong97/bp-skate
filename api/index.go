package handler

import (
	"encoding/json"
	"fmt"
	"io/ioutil"
	"log"
	"net/http"
	"sort"
	"strconv"
	"strings"
	"time"
)

// direct handler for serverless invocation
func Handler(w http.ResponseWriter, r *http.Request) {
	// Basic validation, exits early if not authorized
	origin := r.Header.Get("token")
	if origin != "Andrew" {
		w.WriteHeader(http.StatusForbidden)
		w.Write([]byte("Forbidden"))
		return
	}

	// Get date and make request
	date := r.Header.Get("startDate")
	dateObj, _ := time.Parse("2006-01-02", date)
	sb := makeRequestAndReturnFormattedTimes(date, dateObj)

	// Write outgoing formatted response
	w.WriteHeader(http.StatusOK)
	w.Header().Set("Content-Type", "text/plain")
	w.Write([]byte(sb.String()))
}

func makeRequestAndReturnFormattedTimes(date string, dateObj time.Time) strings.Builder {
	// Query BP API for times
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
			if len(k) == 3 {
				k = "0" + k
			}
			cleanedMap[k] = v
		}
	}

	// Go Maps do not iterate in insertion order, so we have to hack it to do so
	// create slice and store keys
	keys := make([]string, 0, len(cleanedMap))
	for k := range cleanedMap {
		keys = append(keys, k)
	}
	// sort the slice by keys
	sort.Strings(keys)

	var sb strings.Builder
	sb.WriteString("For " + dateObj.Format("Jan 2, 2006") + ":\n")
	// iterate by sorted keys
	for _, skateTime := range keys {
		timeObj, _ := time.Parse("1504", skateTime)
		sb.WriteString(timeObj.Format("3:04 PM") + " has " + strconv.Itoa(cleanedMap[skateTime]) + " spots\n")
	}
	fmt.Println("Successfully formatted response")
	return sb
}
