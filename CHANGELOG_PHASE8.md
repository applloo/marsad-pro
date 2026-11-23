# مرصد الأخبار | تطوير حزم التحليل - المرحلة 7

## ما تم تنفيذه
- إضافة وحدة `analysis_packages.py` لبناء حزم تحليل مستقلة مع لقطة ثابتة من مواد القضية وسجل الادعاءات والأحداث.
- اختيار خيط أو أكثر من الخيوط الآلية أو الخيوط اليدوية؛ وإثراء الحزمة بمواد الأرشيف المطابقة للخيوط المختارة دون تعديل الملف البحثي الأصلي.
- اختيار برومبت من المكتبة الحالية أو استخدام برومبت الملف البحثي الشامل.
- تسجيل النموذج المستهدف (Gemini، OpenRouter، Ollama، Hugging Face، Colab، أو نسخ يدوي).
- حفظ إصدارات الحزم مع بصمة SHA-256 لتحديد اختلاف اللقطة.
- تصدير Markdown وTXT وJSON.
- إضافة `analysis_packages` إلى مخطط التخزين والترحيل والدمج مع الحفاظ على توافق البيانات القديمة.
- لا يتم استدعاء أي API مدفوع عند إنشاء الحزمة؛ اختيار Gemini حالياً يحدد وجهة الاستخدام فقط.

## الاختبارات
- اجتازت اختبارات الوحدات الحالية واختبارات الحزم الجديدة.
- فحص ترجمة ملفات Python باستخدام `compileall`.

## ما لم يدخل هذه الدفعة بعد
- إرسال الحزمة مباشرة إلى Gemini أو مزود آخر.
- قياس الرصيد/الفوترة الفعلية من Google Cloud.
- تقسيم الحزم الضخمة آلياً إلى دفعات سياقية وإعادة دمج المخرجات.
- ربط Colab عبر واجهة تشغيل موثوقة.

## Phase 8 · AI Hub and free-provider connectors
- Added `ai_providers.py` with Gemini, OpenRouter free router, Groq, Cloudflare Workers AI, and local Ollama connectors.
- Added explicit send action only; no background or automatic model calls.
- Added free-tier confirmations, Gemini paid-mode gate, user-entered token prices, monthly budget check with 50% estimation buffer, and token/cost usage history.
- Added saved AI outputs linked to their case and package; API keys remain outside Gist and source files.
- Added `AI_PROVIDERS.md` and optional free Colab notebook for CSV deduplication and exploratory clustering.
- Colab is optional and not required for application runtime.

## Phase 8.1 · أرشيف نتائج التحليل
- إضافة استعراض نتائج الذكاء الاصطناعي المحفوظة لكل قضية من التخزين الدائم، بما يسمح باسترجاعها بعد انتهاء جلسة Streamlit أو فتح التطبيق من جديد.
- عرض المزود والنموذج ووقت التنفيذ وعدد التوكنز المسجل والتكلفة التقديرية مع إمكانية تنزيل النتيجة.
- تمييز كل نتيجة بمعرفها لتفادي تداخل الاختيارات عند تنفيذ أكثر من تحليل في الدقيقة نفسها.
- لم يتغير سلوك إرسال الطلبات: لا إرسال تلقائياً، والإرسال ما زال محصوراً في حساب المالك.


## Phase 8.2 · مسار المخرجات التحريرية
- إضافة اختيار شكل المخرج عند تجهيز حزمة القضية: تحليل استخباراتي، سكريبت مصري، أو تحليل يتبعه سكريبت مستقل.
- إضافة تحديد الجمهور المستهدف ومدة السكريبت.
- تضمين تعليمات تحريرية للعامية المصرية الطبيعية، والخطاف الافتتاحي، وسياق المصالح، والخاتمة، مع فصل المصادر عن نص الإلقاء.
- تعزيز قواعد التحقق: فصل الوقائع عن الادعاءات والاستنتاجات والسيناريوهات، وعدم اختلاق الأرقام أو الاقتباسات أو الروابط، والتنبيه إلى إعادة نشر المصدر الواحد.
- حفظ إعدادات المخرج داخل كل إصدار من الحزمة وتضمينها في تصدير Markdown/TXT/JSON.
- لم تتغير مفاتيح Streamlit Secrets أو بنية GitHub Gist أو مفاتيح التخزين الحالية.

## Phase 8.3 · Content Production Studio
- إضافة `content_factory.py` لبناء تكليفات إنتاج محتوى انطلاقاً من نتائج تحليل محفوظة، مع أنماط: حزمة كاملة، فيديو طويل، ريلز/شورتس، ومنشورات وعناوين.
- إضافة مواصفات الجمهور والمنصة واللهجة والمدة إلى تكليف الإنتاج.
- تضمين ضوابط تحريرية تمنع اختلاق الوقائع، وتفصل الوقائع عن الادعاءات والاستنتاجات والسيناريوهات، وتعلّم المعلومات الناقصة بوضوح.
- إضافة استوديو إنتاج داخل ملف القضية يتيح اختيار نتيجة محفوظة وتجهيز التكليف وتصديره TXT/JSON.
- حفظ تكليفات الإنتاج في `content_jobs` داخل التخزين الدائم، مع توافق رجعي للبيانات القديمة وعدم المساس بمجموعات التخزين الموجودة.
- تجهيز التكليف لا يرسل طلباً ولا يستهلك توكنز. أضيف زر إرسال صريح يستخدم مزود ونموذج AI Hub المختارين، مع احترام صلاحية المالك وتأكيد الخطة المجانية وسقف Gemini المدفوع.
- حفظ المخرجات المنتجة في `content_results` وسجل الاستخدام `ai_usage` مع ربطها بتكليف الإنتاج والقضية، وإتاحة استرجاعها وتنزيلها.
- الاختبارات: 37 ناجحة.

## Phase 8.4 · Visual Production Blueprint
- توسيع مخرجات الحزمة الكاملة والفيديو الطويل والريلز لتشمل Storyboard مفصلاً، وتوقيت المشاهد، ولقطات B-roll، وبرومبتات بصرية مستقلة، وتصميمات صور مصغرة.
- إضافة نوع إنتاج مستقل «خطة بصرية فقط» لمن يريد تجهيز التصوير والمونتاج دون إعادة كتابة السكريبت.
- فرض فصل صريح بين الأرشيف الحقيقي والتصورات المولدة، ومنع تقديم المشاهد التوضيحية كأدلة فوتوغرافية.
- إضافة تعليمات عملية لنسب الأبعاد، ونصوص الشاشة، ومساحات العناوين، وخطة المونتاج والصوت، وربط كل مشهد بمعلومة من التحليل.
- لا يتم توليد الصور أو الفيديو تلقائياً؛ المخرجات تتضمن برومبتات قابلة للنسخ إلى أدوات التوليد التي يختارها المستخدم.


## Phase 8.5 · خريطة المونتاج التنفيذية
- إضافة نوع إنتاج مستقل «خريطة مونتاج تنفيذية» لمن لديه سكريبت أو يريد تجهيز خطة التنفيذ دون إعادة كتابة المحتوى من الصفر.
- إلزام النموذج بتقسيم الإلقاء إلى وحدات U مرقمة وربط كل وحدة بمشهد ولقطة محددين، مع نقل النص المنطوق حرفياً.
- إضافة Asset Manifest بمعرفات أصول وحالة واضحة، ومنع الادعاء بوجود ملفات لم يتم توفيرها أو التحقق منها.
- إضافة جدول EDL/TSV متعدد المسارات للفيديو والجرافيك والتعليق والموسيقى والمؤثرات، بتوقيتات تقديرية قابلة للضبط بعد التسجيل.
- إضافة ترتيب تنفيذ عملي، وخطة منخفضة التكلفة، والتنبيه إلى أن EDL خطة نقل وليست مشروع CapCut/Filmora جاهزاً للفتح.
- يظهر نوع الإنتاج الجديد تلقائياً في قائمة الاستوديو الحالية دون تغيير بنية التخزين أو مفاتيح الأسرار.

## Phase 8.6 — حزمة الإنتاج القابلة للنقل
- إضافة `production_bundle.py` لإنشاء أرشيف ZIP من مخرجات الإنتاج المحفوظة.
- تضمين النص الكامل، ولوحة المشاهد والبرومبتات عند وجود أقسام واضحة، وسجل أصول CSV، وقالب EDL/TSV، وبيانات التكليف، وقائمة تدقيق قبل النشر.
- إضافة زر تنزيل حزمة الإنتاج الكاملة داخل استوديو الإنتاج بعد توليد المحتوى.
- توضيح أن الحزمة لا تحتوي صوراً أو فيديوهات فعلية ما لم تُنتج أو تُرفق، ولا تدّعي إنشاء مشروع مونتاج أصلي.
- إضافة اختبارات لتكوين الأرشيف والتحقق من محتوياته ومعالجة غياب المخرجات.


## Phase 8.7 — محرك توليد صور المشاهد (OpenAI Images API)

- إضافة `image_generation.py` كطبقة مستقلة لتوليد الصور عبر Images API الرسمي، مع اختيار `gpt-image-2` أو `gpt-image-1.5` أو `gpt-image-1-mini`.
- دعم المقاسات المربعة والأفقية والرأسية، واختيار جودة low/medium/high.
- استخدام مفتاح `OPENAI_API_KEY` من Streamlit Secrets، أو إدخاله للجلسة الحالية فقط؛ لا يُحفظ المفتاح في Gist أو سجل النتائج.
- إضافة استوديو صور داخل مخرجات الإنتاج: معرّف مشهد، برومبت، توليد فعلي، معاينة، تنزيل PNG، وحذف من الجلسة. إعادة التوليد تنشئ نسخة جديدة مرقمة للمشهد بدلاً من الكتابة فوق الصورة السابقة.
- تحديث `production_bundle.py` لإضافة الصور المولدة إلى `08_generated_images/` وبياناتها إلى `09_generated_images_manifest.json`.
- الصور تبقى في ذاكرة جلسة Streamlit فقط لتجنب تخزين ملفات ثنائية كبيرة داخل Gist؛ يجب تنزيل ZIP للاحتفاظ بها بعد انتهاء الجلسة.
- لا يوجد توليد فيديو في هذه المرحلة، ولم يتم إجراء طلب مدفوع فعلي أثناء الاختبار.
- الاختبارات: 47 ناجحاً، مع فحص compileall ناجح.


## Phase 8.8 · توحيد التطوير واستعادة أمان التشغيل والبحث الشامل اليومي

- اعتماد نسخة Phase 8.7 (محرك صور المشاهد) أساساً مع الحفاظ على مراحل استوديو الإنتاج السابقة.
- استعادة حماية `concurrency` في ملفات GitHub Actions الأربعة، مع عدم إلغاء التشغيل الجاري.
- استعادة التوافق مع اسمي سر التخزين `GIST_TOKEN` و`GITHUB_TOKEN` في GitHub Actions.
- إضافة جدولة يومية للبحث الشامل في كل المصادر عند 07:00 UTC (09:00 بتوقيت القاهرة)، مع الإبقاء على التشغيل اليدوي.
- الإبقاء على التقرير اليومي عند 04:00 UTC (06:00 بتوقيت القاهرة).
- إضافة اختبارات تمنع تراجع إعدادات الحماية والأسرار والجدولتين مستقبلاً.
- تحديث قائمة نماذج الصور إلى النماذج الأحدث المتاحة، مع إبقاء النماذج السابقة المتوافقة.
- تقييد المقاسات حسب النموذج: المقاسات المخصصة 16:9 و9:16 متاحة للنماذج المرنة، والنماذج الأقدم تعرض المقاسات القياسية فقط لتجنب رفض الطلب من API.
- إظهار تنبيه داخل الواجهة بأن GPT Image 1.5 مقرر إيقافه في 1 ديسمبر 2026.
- تنظيف ملفات `__pycache__` وملفات `.pyc` من حزمة التسليم.
- لم يتم تنفيذ تشغيل حي على GitHub أو Streamlit أو إرسال طلب فعلي إلى OpenAI Images API.

## Phase 8.9 · ربط مزودات ونماذج إضافية
- إضافة مزود مخصص لأي خدمة تقدم واجهة OpenAI Chat Completions متوافقة.
- السماح بإدخال Model ID الخاص بـGemini بدلاً من قائمة ثابتة فقط.
- إضافة إدخال عنوان API واسم النموذج ومفتاح الخدمة المخصصة داخل AI Hub.
- مفاتيح المزود المخصص تبقى في جلسة Streamlit ولا تدخل في Gist أو ملفات القضية.
- اشتراط HTTPS لعناوين المزود المخصص.
- إضافة تأكيد مجاني أو أسعار توكنز وسقف إنفاق شهري للمزود المخصص.
- احتساب سقف المزود المخصص من سجل إنفاق هذا المزود، مع تسجيل التكلفة التقديرية.
- توسيع اختبارات موصلات الذكاء الاصطناعي.

## Phase 8.10 — Human-approved Auto AI Router
- Added task-aware routing suggestions for information extraction, event linking, geopolitical analysis, Egyptian-dialect scripts, and content production.
- Router recommendations are advisory only. The user can override the provider/model and must explicitly approve each model request.
- Added task-specific prompt assembly that combines the saved case snapshot, source material, original analysis prompt, and the selected task instructions.
- Added a full prompt preview and downloadable conversation-ready prompt so the user can run the work in an external AI chat without using an API.
- Added pre-send token estimates and visible cost estimates for paid text-model requests, plus explicit approval and monthly provider-cap checks.
- Added a separate approval and cost gate for content-production requests.
- Added image-generation price entry and confirmation based on the current official price for the selected model/quality/size. The user-supplied confirmed price is recorded in usage history; the app does not invent image prices.
- Logged task type, prompt size, estimate, and actual/estimated cost metadata where available.
- Added unit tests for task prompt construction and provider recommendation.
- GitHub note: the app's existing Gist persistence syncs application DATA, not source-code commits. Source-code deployment still requires committing/pushing this release to the connected repository; Streamlit Cloud can then redeploy from that repository. No repository credentials or connected GitHub push action were available in this build session, so no push/deployment is claimed.

## Phase 8.11 — Prompt Workbench
- Added persistent prompt library with categories and descriptions.
- Every prompt edit creates a new immutable version with timestamp and SHA-256 fingerprint.
- Added version history, rollback as a new version, archive/restore, and TXT download.
- Integrated saved prompts into research-case analysis package creation without removing built-in prompts.
- Added backward-compatible `prompt_library` storage and tests.
- Added `AUDIT_AND_ROADMAP.md` documenting implemented, partial, unverified, and remaining work.

## Phase 8.12 — data integrity and billing profiles
- Added baseline-aware three-way merge for owner Gist data; overlapping stale-session edits are surfaced and the save is stopped instead of silently overwriting the remote version.
- Added persistent per-provider/per-model billing profiles with input/output pricing, local monthly budget, optional pricing source URL, and last-reviewed timestamp.
- Gemini and custom paid analysis paths now reuse saved model-specific billing profiles and check spend against that model's local budget before sending.
- Kept per-workflow GitHub Actions concurrency groups. A shared group was intentionally not used because GitHub concurrency can replace pending runs, potentially dropping scheduled/manual tasks.
- Limitations remain: Gist updates are not atomic transactions, local budgets are not provider-side hard caps, and estimates are not invoices.

## Phase 8.13 - Prompt Workbench Pro
- Added reusable prompt variables with missing/unknown variable diagnostics and filled-prompt export.
- Added multi-case research snapshots with URL-based deduplication and per-case provenance.
- Added six resumable manual prompt-chain stages from extraction through production planning.
- Added same-stage cross-chain comparison prompts, final human approval, and SHA-256 output fingerprinting.
- Persisted `prompt_bundles` and `prompt_chains` in the existing store merge flow.
- Preserved the Phase 8.11 prompt library/version APIs and archive/restore behavior.

## Phase 8.14 — Gist Backup & Recovery
- Added compressed point-in-time Gist snapshots with per-file SHA-256 checksums and a backup manifest.
- Added configurable backup retention and a weekly GitHub Actions backup workflow with manual dispatch.
- Added Streamlit controls to create, inspect, and explicitly restore a selected backup.
- Restore validates the archive and JSON payloads, creates a pre-restore safety snapshot, then restores the snapshot file set.
- Added local unit tests for archive integrity, corruption rejection, mocked Gist backup writes, and workflow schedule wiring.
- Limitations: Gist operations are not atomic; snapshots remain in the same Gist/account and are not independent off-site backups. No live Gist, GitHub Actions, Streamlit, GitHub push, or deployment test was performed.

## Phase 8.15 — Spend Reservations & Workflow Visibility
- Added persistent-intent spend reservations scoped to provider/model/month, with pending, settled, released, failed, and expiry handling.
- Added budget preflight that includes committed usage and unexpired reservations.
- Added reservation-before-request and merged-store recheck to paid text analysis and content-generation requests; failed reservation persistence/conflict stops the paid call when Gist persistence is configured.
- Added the same reservation and budget guard to image generation, including a required monthly image budget alongside user-reviewed image unit pricing and explicit per-image approval.
- Added a recent-run overview for all five GitHub Actions workflows in the operations room.
- Kept independent workflow concurrency groups; no unsafe global concurrency group or false claim of a durable central queue was introduced.
- Limitations: Gist remains non-transactional, so reservation coordination is best-effort rather than a hard distributed lock. Local budgets are not provider-side billing caps. Without Gist persistence, reservations are session-local.

## Phase 8.16 — Independent Off-site Backup Export & Restore
- Added portable ZIP export from a selected, verified Gist snapshot, with a manifest and SHA-256 checksums for each data file.
- Added strict archive validation for schema, duplicate entries, path traversal, file-set consistency, checksums, and JSON validity.
- Added UI download for user-held off-site ZIP archives and guarded import/restore to Gist after creating a pre-restore safety snapshot.
- The ZIP is independent of GitHub only after the user downloads and stores it elsewhere; no external storage integration or encryption is claimed.
- Limitations: Gist restore is still non-atomic; no live Gist/Streamlit/browser/recovery-drill test or GitHub push/deploy was performed.

## Phase 8.17
- Added client-side AES-256-GCM encryption for portable off-site backups, with PBKDF2-HMAC-SHA256 key derivation (600,000 iterations), random salt and nonce.
- Added `.mrbak` encrypted archive export/import in the Streamlit backup UI. Passwords are not saved to Gist or app settings.
- Decryption authenticates the ciphertext and validates the inner ZIP manifest and SHA-256 checksums before restore.
- Added tests for encrypted round-trip, wrong password, ciphertext tampering, and minimum passphrase length.
- Local validation: 85 tests passed; Python compilation passed. Live services and deployment were not tested.

## Phase 8.18 — Source Intelligence Expansion & Paid-Article Radar
- Audited and expanded the source registry to 263 unique domains across Israeli, US, UK, regional, international, African, Asian, and official sources.
- Expanded the intelligence-office registry to 119 sources/organizations, including official US/UK/Israeli public-information channels and specialist defense sources.
- Added a standalone paid/limited-access article radar with a 33-publisher watchlist, public Tactical Report index/newsletter discovery, Google News RSS and GDELT headline search, and Arabic headline translation.
- Added discovery of likely related coverage across 64 open-source domains using Google News RSS and GDELT, with match labels, approximate headline similarity, original links, and legal search/access routes.
- Added direct-only reading and Arabic translation of publicly accessible alternative articles; paid publisher article bodies are not fetched by this feature.
- Added a guard preventing the existing proxy/archive fallback from being used on known paywalled domains.
- At the user's request, removed the dedicated backup UI, scheduled backup workflow, backup implementation modules/tests, and the `cryptography` dependency. Gist remains for normal app-data persistence.
- Local validation: Python compilation passed; 87 tests passed. No live source crawl, Streamlit browser test, GitHub Actions execution, repository push, or deployment was performed.

## Phase 8.19 — Source Health & Intelligence Clustering
- Added a 299-domain health catalog merged from regional press, official/intelligence, think-tank, and paid-radar source registries.
- Added HTTPS availability probes, RSS/Atom autodiscovery, common feed endpoint checks, response timing, HTTP status, latest feed item, and saved-scan comparisons for changed/lost feeds, recovery, new feed items, and temporary reachability failures.
- Added cross-perspective GDELT + Google News RSS collection for American, Israeli, British, and Arabic/regional source groups.
- Added heuristic event clustering, perspective-separated headline narratives, tentative wire/syndication/origin labels, and Arabic headline translation.
- Added unified case dossier JSON export and persistence in the existing Gist app-data store.
- Added GitHub Git Database API release sync from a reviewed ZIP, with path/size/secret filtering, non-force branch update, and optional auto-commit on upload using `GH_SYNC_AUTO=true`.
- Added GitHub Actions CI for compile and unit tests on pushes and pull requests to main.
- No backup feature was reintroduced; Phase 8.18's removal remains in effect.
- Local validation: 102 unit tests passed and Python compilation passed. No live source scan, Streamlit browser run, real GitHub push, CI run, or deployment was performed.

## Phase 8.20 — Entity Intelligence, Timelines & Contradiction Candidates
- Added `entity_intelligence.py` with a curated, expandable alias catalog for people, countries, organizations, military vessels, and military bases, plus the existing case-link entity vocabulary.
- Added entity index with per-mention source URL, publisher/domain, publication timestamp, matched alias, and links to existing research-case IDs.
- Added a chronological publication timeline. It explicitly labels timestamps as publication times, not event-occurrence times.
- Added lexical contradiction candidates using overlapping claim text and opposing polarity markers. Every candidate retains both source records and is labeled for human review; it is not a truth verdict.
- Added article-to-existing-case matching using the established case-link similarity engine. Matches are advisory and do not imply causality.
- Added the Arabic UI sub-tab `الكيانات والتناقضات` with entity index, publication timeline, contradiction candidates, prior-case matches, and enriched JSON export.
- No paid AI requests, API spend, live crawl, or GitHub push are triggered by this phase. The existing explicit approval gate remains unchanged.
- No backup/restore features were added.

## Phase 8.21 — Cumulative Intelligence Case File
- Added `case_intelligence.py` for researcher-triggered cumulative case snapshots and change tracking.
- Added evidence ledger versioning for materials, claims, and events, including additions, edits, claim-status changes, removals, and restorations.
- Preserved before/after payloads and source URLs in the history; no silent overwrite of previous evidence versions.
- Added a cumulative prompt for reviewing what changed, what remains supported, and which earlier conclusions need revision or suspension.
- Added an Arabic casebook panel with snapshot metrics, recent change history, and JSON/prompt downloads.
- Added `intel_case_files` to the existing Gist-backed app store and merge normalization.
- No paid AI/API call, automatic search, backup/restore feature, GitHub push, or deployment is triggered.


## Phase 8.25
- Added auditable task lifecycle records and dispatch tracking for daily/search/topic/watch GitHub Actions requests.
- Added stale-task review flags, heartbeat, retry lineage, and task history in Operations.
- Extended Gist store schema with `job_tasks`; no claim of atomic distributed locking.


## Phase 8.26
- Added resumable large-research batching for active case materials, source provenance IDs, chunk prompts, manual output capture, failed-batch retry, progress, and final synthesis prompt.
- Added `research_batches` to the Gist data schema and stable-ID merge handling.
- No automatic AI/API calls or web crawling; no backup/restore.


## Phase 8.27
- Added a manual-first Egyptian Arabic video storyteller with configurable defaults, analytical reading sheet, timed script prompt, production storyboard, Shorts/Reels, publishing kit, revision workflow, and separately versioned artifacts linked to research cases.
- Added persistent `video_projects` store support and case-deletion cascade. No paid API calls or backup/restore features.

## Phase 8.28 — Search, Translation & Automatic Intelligence Pipeline
- Added strict UTC time-window post-filtering for the primary search flow and GitHub Actions search scopes.
- Added automatic Arabic translations of available article snippets for result cards, with explicit missing/failed status.
- Added automatic research-batch generation from collected search results and prompt download.
- Added candidate thread clustering with provenance and caution labels.
- Added six-hour search-all period option. No paid AI API calls or paywall bypasses.
- Validation: 171 tests passed; Streamlit browser and live crawl not run.
