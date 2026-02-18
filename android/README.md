# HearU Android App (Native Kotlin)

You can now **open this `android/` folder directly in Android Studio**.

## What is included (ready-to-import)
- Android project config files:
  - `settings.gradle.kts`
  - `build.gradle.kts`
  - `gradle.properties`
  - `app/build.gradle.kts`
  - `app/proguard-rules.pro`
- App manifest + resources + Kotlin activities.

## Implemented app screens
- `OnboardingActivity` (welcome + get started)
- `AuthActivity` (login/sign-up UI)
- `ChatActivity` (human/AI support session UI)
- `SettingsActivity` (privacy and notifications)
- `ProfileActivity` (profile update + session context)

## Quick start in Android Studio
1. Open Android Studio.
2. Click **Open** and select the `android/` directory.
3. Let Gradle sync finish.
4. Run app on emulator/device.

If sync asks for JDK, use **JDK 17**.

## Key source files
- `app/src/main/AndroidManifest.xml`
- `app/src/main/java/com/dataman/support/ui/*.kt`
- `app/src/main/res/layout/*.xml`
- `app/src/main/java/com/dataman/support/ApiContracts.kt`

## Next build steps
1. Wire API calls in activities/viewmodels using `ApiContracts.kt`.
2. Add secure token storage (`EncryptedSharedPreferences`).
3. Move UI state into MVVM (`ViewModel` + repository).
4. Replace placeholder chat response with backend/LLM response.

---

## Play Store release path (recommended)

### 1) Technical readiness
- Replace placeholders with real backend integration.
- Add robust validation, error states, loading states, retry handling.
- Add privacy policy URL + terms of use.
- Add safety disclaimers: app is not crisis/clinical emergency support.

### 2) Google Play prerequisites
- Create Google Play Console account.
- Create app entry (`HearU`) and package name (e.g., `com.hearu.app`).
- Prepare assets:
  - App icon (512x512)
  - Feature graphic (1024x500)
  - Screenshots (phone/tablet)
  - Short and full descriptions

### 3) Signing & build
- Generate release keystore.
- Build signed Android App Bundle (`.aab`) in Android Studio.
- Use Play App Signing.

### 4) Policy compliance (critical for this domain)
- Privacy policy with data handling specifics.
- User-generated content policy compliance (reporting, blocking, moderation flow).
- Health/mental wellbeing disclaimers and no misleading medical claims.
- Data safety form completion in Play Console.

### 5) Testing tracks
- Upload to **Internal testing** first.
- Validate onboarding, auth, chat, report flow, crash-free stability.
- Promote to **Closed testing**, gather feedback, then **Production**.

### 6) Post-launch operations
- Set up crash analytics (Firebase Crashlytics).
- Add product analytics events (funnels, retention).
- Prepare moderation escalation SOP for reports/safety events.
