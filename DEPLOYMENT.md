# Demo Deployment

The complete application is packaged as one Docker web service. The React
frontend, logging gateway, and all 17 Flask modules share one public URL.
MongoDB runs separately on MongoDB Atlas.

## 1. Create the MongoDB database

1. Create a free MongoDB Atlas cluster.
2. Create a database user with a strong, unique password.
3. In Atlas Network Access, allow Render to connect. For a short classroom
   demo, `0.0.0.0/0` is the simplest option; remove it after the demo.
4. Copy the connection string and replace its username and password:

   `mongodb+srv://USERNAME:PASSWORD@CLUSTER.mongodb.net/?retryWrites=true&w=majority`

## 2. Deploy on Render

1. In Render, choose **New > Blueprint** and connect this GitHub repository.
2. Render will read `render.yaml` and create the `secure-exam-system` service.
3. Enter these secret environment values when prompted:

   - `MONGO_URI`: the Atlas connection string.
   - `DEMO_OTP`: optional six-digit demo code such as `123456`.
   - `SMTP_HOST`: SMTP host for real OTP email delivery.
   - `SMTP_PORT`: usually `587`.
   - `SMTP_USERNAME`: SMTP account username.
   - `SMTP_PASSWORD`: SMTP account password or app password.
   - `SMTP_FROM_EMAIL`: sender email address.
   - `SMTP_USE_TLS`: `true` for most SMTP providers.

4. Deploy the Blueprint and wait for `/healthz` to report healthy.

The generated Render URL is the complete application URL. All API requests are
same-origin, so no extra frontend configuration is required.

## Demo notes

- `DEMO_OTP` is optional. For a real demo with email OTPs, remove `DEMO_OTP`
  and configure the SMTP variables above.
- If SMTP is configured, OTPs are emailed to the registered email address.
- If SMTP is not configured, the authentication module falls back to the fixed
  `DEMO_OTP` or prints a random development OTP to service logs.
- OTPs are never returned by the login API.
- A sleeping free service can take a little while to answer its first request.
- Remove the broad Atlas network rule and delete or suspend the demo service
  after the presentation.

## Local container smoke test

With MongoDB running on the host:

```powershell
docker build -t secure-exam-system .
docker run --rm -p 10000:10000 `
  -e MONGO_URI=mongodb://host.docker.internal:27017/ `
  -e JWT_SECRET=local-demo-secret `
  -e DEMO_OTP=123456 `
  -e SMTP_HOST=smtp.example.com `
  -e SMTP_PORT=587 `
  -e SMTP_USERNAME=your_smtp_username `
  -e SMTP_PASSWORD=your_smtp_password `
  -e SMTP_FROM_EMAIL=no-reply@example.com `
  -e LOGGING_GATEWAY_URL=http://127.0.0.1:10000/api/logs/write `
  -e MODULE_BASE_URL=http://127.0.0.1:10000 `
  secure-exam-system
```

Open `http://localhost:10000` and check `http://localhost:10000/healthz`.
