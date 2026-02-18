# HearU Android App (Native Kotlin)

This directory now contains a multi-screen Android app starter for HearU:

## Implemented app screens
- `OnboardingActivity` (welcome + get started)
- `AuthActivity` (login/sign-up UI)
- `ChatActivity` (human/AI support session UI)
- `SettingsActivity` (privacy and notifications)
- `ProfileActivity` (profile update + session context)

## Key source files
- `app/src/main/AndroidManifest.xml`
- `app/src/main/java/com/dataman/support/ui/*.kt`
- `app/src/main/res/layout/*.xml`
- `app/src/main/java/com/dataman/support/ApiContracts.kt`

## Next build steps (Android Studio)
1. Create/attach Gradle project files (`build.gradle`, `settings.gradle`, wrapper) if not already present.
2. Add dependencies:
   - `androidx.appcompat`
   - `material`
   - `retrofit2`, `okhttp`
   - `kotlinx-serialization` or `moshi`
3. Set `minSdk` (e.g., 24+) and `targetSdk` (latest stable).
4. Wire API calls in activities/viewmodels using `ApiContracts.kt` models.
5. Add secure token storage (`EncryptedSharedPreferences`).

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
- Use Play App Signing (recommended by Google).

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
