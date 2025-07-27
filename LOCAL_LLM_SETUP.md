# Local LLM Setup for AI Code Review Agent

The AI Code Review Agent is configured to use a local LLM server for code analysis. This document explains how to set up and run a local LLM server using LM Studio.

## Option 1: LM Studio (Recommended)

### Step 1: Download and Install LM Studio
1. Visit [https://lmstudio.ai/](https://lmstudio.ai/)
2. Download LM Studio for your operating system
3. Install and launch LM Studio

### Step 2: Download a Compatible Model
1. In LM Studio, go to the "Discover" tab
2. Search for and download one of these recommended models:
   - **Lily Cybersecurity 7B** (recommended for code security analysis)
   - **Code Llama 7B** (good for general code analysis)
   - **Mistral 7B Instruct** (balanced performance)
   - **Phi-3 Mini** (lightweight option)

### Step 3: Start the Local Server
1. Go to the "Local Server" tab in LM Studio
2. Select your downloaded model
3. Configure the server settings:
   - **Port**: 4000 (or update docker-compose.yml if using different port)
   - **CORS**: Enable
   - **API Format**: OpenAI Compatible
4. Click "Start Server"
5. The server will be available at `http://localhost:4000`

### Step 4: Test the Connection
```bash
curl -X POST "http://localhost:4000/v1/chat/completions" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "your-model-name",
    "messages": [{"role": "user", "content": "Hello"}],
    "max_tokens": 100
  }'
```

## Option 2: Ollama

### Step 1: Install Ollama
```bash
# macOS/Linux
curl -fsSL https://ollama.ai/install.sh | sh

# Or download from https://ollama.ai/download
```

### Step 2: Pull a Model
```bash
ollama pull codellama:7b
# or
ollama pull mistral:7b
```

### Step 3: Start Ollama Server
```bash
ollama serve --port 4000
```

## Option 3: Other Local LLM Servers

You can use any OpenAI-compatible local LLM server. Update the configuration in `docker-compose.yml`:

```yaml
environment:
  - LOCAL_LLM_BASE_URL=http://host.docker.internal:YOUR_PORT
  - LOCAL_LLM_MODEL=your-model-name
```

## Configuration

### Environment Variables
The application uses these environment variables for Local LLM configuration:

- `DEFAULT_LLM_PROVIDER=local` - Use local LLM instead of OpenAI/Anthropic
- `LOCAL_LLM_BASE_URL=http://host.docker.internal:4000` - URL of your local LLM server
- `LOCAL_LLM_MODEL=lily-cybersecurity-7b-v0.2` - Model name to use

### Docker Network Access
When running in Docker, use `host.docker.internal:4000` instead of `localhost:4000` to access the host machine's LLM server.

## Fallback Behavior

If the Local LLM server is not available, the application will:
1. Log a connection error
2. Return a mock analysis with sample security findings
3. Continue processing without failing

This allows the application to run even without a Local LLM server for demonstration purposes.

## Troubleshooting

### Connection Issues
- Ensure LM Studio or your LLM server is running on port 4000
- Check if the model is loaded and the server is started
- Verify firewall settings allow connections on port 4000

### Performance Issues
- Use smaller models (7B parameters) for faster response times
- Increase timeout settings if needed
- Consider using GPU acceleration if available

### Model Compatibility
- Ensure your model supports OpenAI-compatible chat completions API
- Some models may require specific prompt formats

## Testing the Setup

1. Start your Local LLM server (LM Studio, Ollama, etc.)
2. Start the AI Code Review Agent:
   ```bash
   docker-compose up
   ```
3. Submit a repository for analysis:
   ```bash
   curl -X POST "http://localhost:8000/analyze-pr" \
     -H "Content-Type: application/json" \
     -d '{
       "repo_url": "https://github.com/your-repo/example",
       "analysis_type": "comprehensive"
     }'
   ```
4. Check the task status to see the analysis results

The logs should show successful connections to your Local LLM server and real analysis results instead of mock data.
