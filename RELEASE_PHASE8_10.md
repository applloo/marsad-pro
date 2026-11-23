# Marsad News — Phase 8.10

## Human-approved Auto AI Router

### What is new
- Five task profiles: news information extraction, event linking, geopolitical analysis, Egyptian-dialect script writing, and content production.
- A task-aware provider suggestion based only on providers with settings available in the current app session/secrets. The suggestion is not a claim of model availability, quality, or free quota.
- Manual provider/model override remains available.
- No automatic model execution. Every text analysis, content-production request, and image-generation request has a separate explicit approval step.
- Complete conversation-ready prompt assembled from the immutable case package plus task-specific instructions, with preview and TXT download. This supports manual copy/paste into ChatGPT or another external conversation without an API call.
- Pre-send estimated input/output tokens and estimated cost for paid text-model calls. Paid calls require entered prices, price review, an active monthly cap, and explicit approval.
- Separate cost/approval gate for content production.
- Image generation requires the user to enter and confirm the current official price for the selected model, quality, and size before generating. That confirmed amount is recorded in AI usage history.

### Cost and safety notes
- Token counts and text cost projections are estimates, not invoices. Actual provider billing may differ.
- The app never assumes an unknown route is free. If price/billing mode is unknown, the action stays disabled.
- For free-tier routes, the user must explicitly confirm the account is on a free plan and not subject to paid overage.
- Image prices are deliberately not hard-coded because they vary by model/quality/size and may change.
- API keys remain in Streamlit Secrets or the active session; they are not added to Gist data or release files.

### GitHub / deployment
- Existing `persist()` saves application data to the configured private Gist. That is data synchronization, not source-code synchronization.
- To deploy this source release, it must be pushed to the GitHub repository connected to Streamlit Cloud. Streamlit Cloud can then redeploy automatically from the repository.
- This environment did not have access to the user's repository credentials or a GitHub commit/push connector. No GitHub push or Streamlit deployment was performed.

### Validation
- `python -m py_compile *.py`: passed.
- `python -m unittest discover -s tests -q`: 41 tests passed.
- No live Gemini/custom API call, OpenAI image generation call, GitHub push, or Streamlit Cloud deployment was performed.
