# Field Service Mobile (KMP)

Kotlin Multiplatform shared logic + native Android UI (iOS UI later).

**Milestone 4:** agenda + job detail API clients in `shared` (`ApiClient`, `AgendaRepository`) with Android `HttpURLConnection` transport. Device/emulator run is optional for the portfolio demo.

## Modules

- `shared` — models, `ApiClient` (login / agenda / job detail), `AgendaRepository` (live API with demo fallback), expect/actual `HttpTransport`
- `androidApp` — Jetpack Compose agenda list + job detail

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
4. If the API is down, the UI falls back to demo stub jobs (`source=demo`)

### Physical device

Set `ApiClient(baseUrl = "http://<your-lan-ip>:8003/api/v1")` and ensure the phone can reach the host firewall.

## CLI assemble (optional)

```bash
cd products/field-service/mobile
./gradlew :androidApp:assembleDebug
```

Windows: `gradlew.bat :androidApp:assembleDebug`

## Notes

- Acknowledgement / offline sync remain web-first or later milestones
- iOS `HttpTransport` is a Coming Soon stub
- No paid maps, push, or PDF SDKs
