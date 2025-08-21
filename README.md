## Usage

### Environment Setup

1. **Copy the environment template:**
   ```bash
   cp .env.sample .env
   ```

2. **Add your API keys to `.env`:**
   ```bash
   # Required
   GOOGLE_API_KEY=your_google_api_key_here
   
   # Optional - for LLM tracing with Langfuse
   LANGFUSE_PUBLIC_KEY=your_langfuse_public_key
   LANGFUSE_SECRET_KEY=your_langfuse_secret_key
   LANGFUSE_HOST=https://cloud.langfuse.com
   ```

3. **Start the REST API server:**
   ```bash
   python -m personal_agent
   ```

Then you can communicate through continuous api calls in the browser:

![](./img/result.png)


### LLM Observability (Optional)

To enable LLM call tracing with Langfuse:
1. Create a free account at [Langfuse Cloud](https://cloud.langfuse.com) or deploy self-hosted
2. Get your public and secret keys from the project settings
3. Add them to your `.env` file as shown above
4. Restart the server - tracing will automatically activate


## TODO
* Add UI to demonstrate communications
