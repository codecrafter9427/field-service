# Field Service Mobile (KMP)

Kotlin Multiplatform shared logic + native Android UI (iOS UI later).

**Milestone 5:** offline UUID op queue for notes / checklist toggles / work-order status, reconnect drain, and visible conflict resolve (keep local / take server). Never silent overwrite.

## Modules

- `shared` — models, `ApiClient` (login / agenda / job detail + writes), `AgendaRepository`, `OfflineQueue` + `SyncRepository`, expect/actual `HttpTransport`
- `androidApp` — Jetpack Compose agenda → job detail with offline edits, sync badges, conflict UI
- Queue persistence: Android `FileQueueStore` under app files (`offline_sync_queue.txt`)

## Android Studio sync (required to open the project)

1. Install **Android Studio** (Ladybug+ recommended) with **Android SDK 35** and **JDK 17**.
2. **File → Open** → select `products/field-service/mobile` (the folder with `settings.gradle.kts`).
3. Wait for **Gradle Sync**. Accept any SDK license prompts.
4. If sync fails:
   - Confirm JDK 17 under **Settings → Build → Gradle → Gradle JDK**
   - Use the project wrapper (`gradlew`) — do not force an unrelated Gradle version
   - Invalidate caches only if dependency resolution is stuck
5. Select run configuration **androidApp**.
6. Optional: start an emulator or plug in a device with USB debugging.

### Live API from emulator

1. Start Field Service API on the host: `uvicorn app.main:app --reload --port 8003`
2. Emulator uses `http://10.0.2.2:8003/api/v1` (default in `ApiClient`)
3. Login uses demo tech: `tech@demo.local` / `demo`
4. If the API is down for agenda login, the UI falls back to demo stub jobs (`source=demo`); **queued edits still persist locally**

### Physical device

Set `ApiClient(baseUrl = "http://<your-lan-ip>:8003/api/v1")` and ensure the phone can reach the host firewall.

## Airplane-mode demo (M5)

1. Start API `:8003` + seed data; run `androidApp` on emulator with network on.
2. Open a live job (prefer one with a checklist). Confirm detail loads (`updated_at` shown).
3. Enable **Airplane mode** (or disable emulator network).
4. Queue a **note**, toggle a **checklist** item, change **status** — badges show **Pending**.
5. Disable airplane mode → tap **Drain queue** / **Sync now**.
6. Confirm ops sync; web dispatcher timeline shows the note/status/checklist activity.
7. **Conflict path:** with app online, note the job `updated_at`. On web, change the same job status. Offline (or before drain), queue a different status on mobile → drain → **Conflict** badge → choose **Keep local** (retry with fresh base) or **Take server**.

## CLI assemble (optional)

```bash
cd products/field-service/mobile
./gradlew :androidApp:assembleDebug
./gradlew :shared:testDebugUnitTest
```

Windows: `gradlew.bat :androidApp:assembleDebug`

## Notes

- Offline scope is **notes + checklist + status only** (no attachments / signoff / time offline)
- iOS `HttpTransport` remains a Coming Soon stub
- No paid maps, push, or PDF SDKs
