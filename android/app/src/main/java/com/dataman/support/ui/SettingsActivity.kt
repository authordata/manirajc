package com.dataman.support.ui

import android.os.Bundle
import android.widget.Switch
import android.widget.TextView
import com.dataman.support.R

class SettingsActivity : BaseActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_settings)

        val summary = findViewById<TextView>(R.id.settingsSummary)
        val anonymousSwitch = findViewById<Switch>(R.id.anonymousSwitch)

        anonymousSwitch.setOnCheckedChangeListener { _, isChecked ->
            summary.text = if (isChecked) {
                "Anonymous mode is ON"
            } else {
                "Anonymous mode is OFF"
            }
        }

        wireBottomNav(active = 2)
    }
}
