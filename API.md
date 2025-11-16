# Bryant Park Skate Availability API

A RESTful API for querying ice skating availability times at Bryant Park. This API fetches data from the Peek booking system and provides it in JSON and human-readable text formats.

## Overview

The API provides two main endpoints for querying availability:

- **Single Date**: Get availability for a specific date (or current date if not specified)
- **Date Range**: Get availability across a range of dates

Both endpoints support:

- JSON responses (default, `caller=API`)
- Human-readable text format (via `caller=USER` parameter)
- Automatic filtering of time slots with 0 available spots

---

## Endpoints

### 1. Root Endpoint

**GET** `/`

Returns API information and available endpoints.

#### Response

```json
{
  "message": "Bryant Park Skate Availability API",
  "endpoints": {
    "/availability?date=YYYY-MM-DD": "Get availability for a single date. If not provided, uses current date.",
    "/availability-range?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD": "Get availability for a date range. If not provided, uses current date."
  },
  "example": {
    "/availability?date=2025-11-16": "Get availability for November 16, 2025",
    "/availability-range?start_date=2025-11-16&end_date=2025-11-23": "Get availability for November 16-23, 2025"
  }
}
```

---

### 2. Single Date Availability

**GET** `/availability`

Get availability times for a single date.

#### Query Parameters

| Parameter | Type   | Required | Default      | Description                                                                       |
| --------- | ------ | -------- | ------------ | --------------------------------------------------------------------------------- |
| `date`    | string | No       | Current date | Date in format `YYYY-MM-DD` (e.g., "2025-11-16")                                  |
| `caller`  | enum   | No       | `API`        | Caller type: `USER` returns human-readable text format, `API` returns JSON format |

#### Examples

**Get availability for a specific date (JSON):**

```bash
GET /availability?date=2025-11-16
```

**Get availability for today (JSON):**

```bash
GET /availability
```

**Get availability in human-readable format:**

```bash
GET /availability?date=2025-11-16&caller=USER
```

#### JSON Response Format

```json
{
  "date": "2025-11-16",
  "count": 10,
  "times": [
    {
      "time": "7:20PM",
      "date": "2025-11-16",
      "spots": 36,
      "availability_mode": "available",
      "start_time": "2025-11-16T19:20:00",
      "end_time": "2025-11-16T20:30:00"
    },
    {
      "time": "7:30PM",
      "date": "2025-11-16",
      "spots": 38,
      "availability_mode": "available",
      "start_time": "2025-11-16T19:30:00",
      "end_time": "2025-11-16T20:40:00"
    }
  ]
}
```

#### Text Response Format (`caller=USER`)

```
For November 16, 2025:
7:20PM has 36 spots
7:30PM has 38 spots
8:40PM has 29 spots
8:50PM has 35 spots
9:00PM has 39 spots
9:10PM has 43 spots
10:20PM has 45 spots
10:30PM has 42 spots
10:40PM has 45 spots
10:50PM has 42 spots
```

**Note:** Time slots with 0 spots are automatically filtered out.

---

### 3. Date Range Availability

**GET** `/availability-range`

Get availability times across a date range.

#### Query Parameters

| Parameter    | Type   | Required | Default | Description                                                                       |
| ------------ | ------ | -------- | ------- | --------------------------------------------------------------------------------- |
| `start_date` | string | **Yes**  | -       | Start date in format `YYYY-MM-DD`                                                 |
| `end_date`   | string | **Yes**  | -       | End date in format `YYYY-MM-DD`                                                   |
| `caller`     | enum   | No       | `API`   | Caller type: `USER` returns human-readable text format, `API` returns JSON format |

#### Examples

**Get availability for a date range (JSON):**

```bash
GET /availability-range?start_date=2025-11-16&end_date=2025-11-23
```

**Get availability in human-readable format:**

```bash
GET /availability-range?start_date=2025-11-16&end_date=2025-11-23&caller=USER
```

#### JSON Response Format

```json
{
  "start_date": "2025-11-16",
  "end_date": "2025-11-23",
  "count": 45,
  "times": [
    {
      "time": "7:20PM",
      "date": "2025-11-16",
      "spots": 36,
      "availability_mode": "available",
      "start_time": "2025-11-16T19:20:00",
      "end_time": "2025-11-16T20:30:00"
    },
    {
      "time": "7:30PM",
      "date": "2025-11-16",
      "spots": 38,
      "availability_mode": "available",
      "start_time": "2025-11-16T19:30:00",
      "end_time": "2025-11-16T20:40:00"
    },
    {
      "time": "8:00AM",
      "date": "2025-11-17",
      "spots": 20,
      "availability_mode": "available",
      "start_time": "2025-11-17T08:00:00",
      "end_time": "2025-11-17T09:10:00"
    }
  ]
}
```

#### Text Response Format (`caller=USER`)

```
For November 16, 2025:
7:20PM has 36 spots
7:30PM has 38 spots
8:40PM has 29 spots

For November 17, 2025:
8:00AM has 20 spots
9:00AM has 25 spots
10:00AM has 30 spots

For November 18, 2025:
7:00PM has 40 spots
8:00PM has 35 spots
```

**Note:**

- Time slots with 0 spots are automatically filtered out
- Times are grouped by date
- Dates are sorted chronologically

---

## Data Models

### AvailabilityTime

Represents a single availability time slot.

```typescript
{
  time: string;              // Display time (e.g., "7:20PM")
  date: string;              // Date in YYYY-MM-DD format
  spots: number;             // Number of available spots
  availability_mode: string; // "available" or "sold_out"
  start_time?: string;       // ISO datetime start (optional)
  end_time?: string;         // ISO datetime end (optional)
}
```

### AvailabilityResponse

Response for single date endpoint.

```typescript
{
  date: string;                    // Date queried
  count: number;                   // Number of available time slots
  times: AvailabilityTime[];       // Array of availability times
}
```

### AvailabilityRangeResponse

Response for date range endpoint.

```typescript
{
  start_date: string;              // Start date of range
  end_date: string;                // End date of range
  count: number;                   // Total number of available time slots
  times: AvailabilityTime[];       // Array of availability times (across all dates)
}
```

---

## Caller Parameter

The `caller` parameter is an enum that determines the response format:

| Value  | Description                                                                        | Response Format           |
| ------ | ---------------------------------------------------------------------------------- | ------------------------- |
| `API`  | Default value. Returns structured JSON data suitable for programmatic consumption. | JSON (`application/json`) |
| `USER` | Returns human-readable plain text format suitable for direct display to end users. | Plain Text (`text/plain`) |

**Default:** If `caller` is not provided, it defaults to `API` (JSON format).

---

## Response Formats

### JSON Format (Default)

When `caller=API` or not provided, the API returns JSON responses with structured data models.

**Content-Type:** `application/json`

### Text Format

When `caller=USER`, the API returns plain text in a human-readable format.

**Content-Type:** `text/plain`

**Format:**

- Single date: `For {Month Day, Year}:\n{time} has {spots} spots\n...`
- Date range: Times grouped by date with blank lines between dates

---

## Error Handling

### Error Response Format

```json
{
  "detail": "Error message describing what went wrong"
}
```

### HTTP Status Codes

| Status Code | Description                                           |
| ----------- | ----------------------------------------------------- |
| 200         | Success                                               |
| 400         | Bad Request (invalid parameters)                      |
| 500         | Internal Server Error (API failure, data fetch error) |

### Common Error Scenarios

**Invalid date format:**

```json
{
  "detail": "Invalid date format: 2025/11/16"
}
```

**Failed to fetch data:**

```json
{
  "detail": "Failed to fetch availability data"
}
```

**General error:**

```json
{
  "detail": "Error: {error message}"
}
```

---

## Features

### Automatic Filtering

- **Zero spots filtered**: Time slots with 0 available spots are automatically excluded from responses
- **Only available times**: Only times with `spots > 0` are returned

### Date Handling

- **Current date default**: If `date` parameter is omitted in `/availability`, the current date is used
- **Date format**: All dates must be in `YYYY-MM-DD` format (ISO 8601 date)

### Response Variations

1. **JSON** (default): Structured data with Pydantic model validation
2. **Text** (`caller=USER`): Human-readable format
