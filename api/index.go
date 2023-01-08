package handler

import (
	"encoding/json"
	"io/ioutil"
	"log"
	"net/http"
	"sort"
	"strconv"
	"strings"
	"time"
)

// Handler code entrypoint
func Handler(w http.ResponseWriter, r *http.Request) {
	// Basic validation, exits early if not authorized
	//origin := r.Header.Get("token")
	//if origin != "Andrew" {
	//	w.WriteHeader(http.StatusForbidden)
	//	w.Write([]byte("Forbidden"))
	//	return
	//}

	// Get date and make request
	date := r.Header.Get("startDate")
	dateObj, dateParseError := time.Parse("2006-01-02", date)
	if dateParseError != nil {
		log.Println("WARNING: bad date input - inputted date:" + date)
	}
	var rawResponse = querySkateTimesAPI(date, w)
	sb := getFormattedTimes(date, dateObj, rawResponse)

	// Write outgoing formatted response
	writeSuccessResponse(w, &sb)
}

func writeSuccessResponse(w http.ResponseWriter, sb *strings.Builder) {
	w.WriteHeader(http.StatusOK)
	w.Header().Set("Content-Type", "text/plain")
	w.Write([]byte(sb.String()))
}

func getFormattedTimes(date string, dateObj time.Time, skateTimesMap map[string]map[string]int) strings.Builder {
	// Remove values where time slot count is 0
	var skateTimesMapNoZeroValues = map[string]int{}
	for k, v := range skateTimesMap[date] {
		if v > 0 {
			if len(k) == 3 {
				k = "0" + k
			}
			skateTimesMapNoZeroValues[k] = v
		}
	}

	// Go Maps do not iterate in insertion order, so we have to hack it to do so
	// create slice and store keys
	var keys = make([]string, 0, len(skateTimesMapNoZeroValues))
	for k := range skateTimesMapNoZeroValues {
		keys = append(keys, k)
	}
	// sort the slice by keys
	sort.Strings(keys)

	return formatSkateTimes(dateObj, keys, skateTimesMapNoZeroValues)
}

func querySkateTimesAPI(date string, w http.ResponseWriter) map[string]map[string]int {
	// Query BP API for times
	res, err := http.Get("https://xola.com/api/experiences/61536b244f19be5b3c6e4241/availability?start=" + date + "&end=" + date + "&privacy=public")
	log.Println("Successfully made outbound request")

	// check for response error
	if err != nil {
		w.WriteHeader(http.StatusInternalServerError)
		log.Fatal(err) // exit early
	}

	// read all response body into string and close stream
	data, _ := ioutil.ReadAll(res.Body)
	res.Body.Close()

	// unpack response into { date: { time: count } } map
	skateTimesMap := map[string]map[string]int{}
	json.Unmarshal(data, &skateTimesMap)
	return skateTimesMap
}

func formatSkateTimes(dateObj time.Time, keys []string, cleanedMap map[string]int) strings.Builder {
	var sb strings.Builder
	sb.WriteString("For " + dateObj.Format("Jan 2, 2006") + ":\n")
	// iterate by sorted keys
	for _, skateTime := range keys {
		timeObj, _ := time.Parse("1504", skateTime)
		sb.WriteString(timeObj.Format("3:04 PM") + " has " + strconv.Itoa(cleanedMap[skateTime]) + " spots\n")
	}
	return sb
}
