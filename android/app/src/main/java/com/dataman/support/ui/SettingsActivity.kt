package com.dataman.support.ui

import android.content.Context
import android.content.Intent
import android.os.Bundle
import com.dataman.support.R
import com.dataman.support.databinding.ActivitySettingsBinding

class SettingsActivity : BaseActivity() {

    private lateinit var binding: ActivitySettingsBinding

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivitySettingsBinding.inflate(layoutInflater)
        setContentView(binding.root)

        setupBottomNavigation(binding.navBottom.bottomNavigationView)
        updateNavigationBarState(binding.navBottom.bottomNavigationView, R.id.nav_settings)

        setupListeners()
        loadPreferences()
    }

    private fun setupListeners() {
        binding.switchAnonymous.setOnCheckedChangeListener { _, isChecked ->
            savePreference("anonymous_mode", isChecked)
        }

        binding.switchNotifications.setOnCheckedChangeListener { _, isChecked ->
            savePreference("notifications", isChecked)
        }

        binding.btnLogout.setOnClickListener {
            val intent = Intent(this, OnboardingActivity::class.java).apply {
                flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
            }
            startActivity(intent)
            finish()
        }
    }

    private fun loadPreferences() {
        val prefs = getSharedPreferences("settings", Context.MODE_PRIVATE)
        binding.switchAnonymous.isChecked = prefs.getBoolean("anonymous_mode", false)
        binding.switchNotifications.isChecked = prefs.getBoolean("notifications", true)
    }

    private fun savePreference(key: String, value: Boolean) {
        getSharedPreferences("settings", Context.MODE_PRIVATE).edit().putBoolean(key, value).apply()
    }
}
