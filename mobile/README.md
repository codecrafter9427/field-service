# Field Service Mobile (KMP)

Kotlin Multiplatform shared logic + native Android UI (iOS UI later).

## Modules

- `shared` — common models, agenda repository stub, API client stub
- `androidApp` — Jetpack Compose shell showing technician agenda placeholders

## Open in Android Studio

1. Open `products/field-service/mobile`
2. Let Gradle sync (requires Android SDK + JDK 17)
3. Run `androidApp` on an emulator/device

## Notes

- Agenda data is fictional stub data from `AgendaRepository`
- No offline sync, signature capture, or real AI in this scaffold
- Backend URL hint for emulator: `http://10.0.2.2:8003/api/v1`
