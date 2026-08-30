package com.dataman.support.ui

import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.widget.RadioButton
import android.widget.RadioGroup
import androidx.appcompat.app.AppCompatDelegate
import com.dataman.support.R
import com.dataman.support.databinding.ActivitySettingsBinding
import com.google.android.material.dialog.MaterialAlertDialogBuilder

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
        binding.layoutAppearance.setOnClickListener {
            showThemeDialog()
        }

        binding.switchAnonymous.setOnCheckedChangeListener { _, isChecked ->
            savePreference("anonymous_mode", isChecked)
        }

        binding.switchNotifications.setOnCheckedChangeListener { _, isChecked ->
            savePreference("notifications", isChecked)
        }

        binding.btnShare.setOnClickListener {
            shareApp()
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

        val hearuPrefs = getSharedPreferences("hearu_prefs", Context.MODE_PRIVATE)
        val currentMode = hearuPrefs.getInt("theme_mode", AppCompatDelegate.MODE_NIGHT_FOLLOW_SYSTEM)
        updateThemeSummary(currentMode)
    }

    private fun updateThemeSummary(mode: Int) {
        binding.tvCurrentTheme.text = when (mode) {
            AppCompatDelegate.MODE_NIGHT_NO -> getString(R.string.light_mode)
            AppCompatDelegate.MODE_NIGHT_YES -> getString(R.string.dark_mode_option)
            else -> getString(R.string.system_default)
        }
    }

    private fun showThemeDialog() {
        val themes = arrayOf(
            getString(R.string.light_mode),
            getString(R.string.dark_mode_option),
            getString(R.string.system_default)
        )
        val currentMode = getSharedPreferences("hearu_prefs", Context.MODE_PRIVATE)
            .getInt("theme_mode", AppCompatDelegate.MODE_NIGHT_FOLLOW_SYSTEM)
        val checkedItem = when (currentMode) {
            AppCompatDelegate.MODE_NIGHT_NO -> 0
            AppCompatDelegate.MODE_NIGHT_YES -> 1
            else -> 2
        }

        MaterialAlertDialogBuilder(this)
            .setTitle(getString(R.string.choose_theme))
            .setSingleChoiceItems(themes, checkedItem) { dialog, which ->
                val mode = when (which) {
                    0 -> AppCompatDelegate.MODE_NIGHT_NO
                    1 -> AppCompatDelegate.MODE_NIGHT_YES
                    else -> AppCompatDelegate.MODE_NIGHT_FOLLOW_SYSTEM
                }
                getSharedPreferences("hearu_prefs", Context.MODE_PRIVATE)
                    .edit().putInt("theme_mode", mode).apply()
                AppCompatDelegate.setDefaultNightMode(mode)
                updateThemeSummary(mode)
                dialog.dismiss()
            }
            .setNegativeButton(android.R.string.cancel, null)
            .show()
    }

    private fun savePreference(key: String, value: Boolean) {
        getSharedPreferences("settings", Context.MODE_PRIVATE).edit().putBoolean(key, value).apply()
    }

    private fun shareApp() {
        val shareIntent = Intent(Intent.ACTION_SEND).apply {
            type = "text/plain"
            putExtra(Intent.EXTRA_SUBJECT, getString(R.string.app_name))
            putExtra(Intent.EXTRA_TEXT, 
                "Someone might need to hear this: You are not alone. " +
                "HearU is a free, anonymous emotional support app. " +
                "Download: https://play.google.com/store/apps/details?id=com.dataman.support")
        }
        startActivity(Intent.createChooser(shareIntent, "Share HearU with someone who might need it"))
    }
}