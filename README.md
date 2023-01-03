## Introduction

Basic Python serverless API that grabs bryant park free skate times. Deployed on [Vercel](https://vercel.com?utm_source=github&utm_medium=readme&utm_campaign=vercel-examples).

## Deployment Configuration

I'm currently deploying the logic as a Python lambda server on Vercel, which is called by the Apple Shortcuts "Get Content" API.
Request flow: User invokes Siri Shortcut, provides date. Apple Shortcut passes the date as a request header to the API host and endpoint. The lambda receives this request, and uses the date header in its call to the Bryant Park API. The lambda reads the BP API response, and sends a plaintext response to Apple Shortcuts, which then displays the formatted text for Siri to read.

## Running in Dev Mode

```bash
npm i -g vercel
vercel dev
```

Your Python API is now available at `http://localhost:3000/api`.

## Creating the Apple Shortcut to call this API

![IMG_4396](https://user-images.githubusercontent.com/7339169/207697487-c54350b5-fa10-445d-acf9-b33e61e7f694.jpg)
