## Introduction

Basic Go serverless API that grabs bryant park free ice skating sessions along with the number of slots. Deployed on [Vercel](https://vercel.com?utm_source=github&utm_medium=readme&utm_campaign=vercel-examples).

## Deployment Configuration

I'm currently deploying the logic as a Go lambda on Vercel, which is called by the Apple Shortcuts "Get Content" API.

Request flow: User invokes Siri Shortcut, provides date. Apple Shortcut passes the date as a request header to the API host and endpoint. The lambda receives this request, and uses the date header in its call to the Bryant Park API. The lambda reads the BP API response, and sends a plaintext response to Apple Shortcuts, which then displays the formatted text for Siri to read.

## Prod Usage

I'm currently limiting access of the API due to rate limiting issues. If you need access, please file a ticket in the [Issues](https://github.com/andrewwong97/bp-skate/issues) tab.

## Running in Dev Mode
You can test the functionality of the outbound request using the legacy Python code by moving `legacy-index.py` from root to `api/` folder (maybe have to delete or temporarily move `index.go`). Currently there is no way to test the Go code besides deploying to staging.

```bash
npm i -g vercel
vercel dev
```

Your Python API is now available at `http://localhost:3000/api`.

## Creating the Apple Shortcut to call this API

![IMG_4396](https://user-images.githubusercontent.com/7339169/207697487-c54350b5-fa10-445d-acf9-b33e61e7f694.jpg)
