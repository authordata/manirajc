package com.dataman.support.ui

import android.os.Bundle
import android.widget.Button
import android.widget.TextView
import com.dataman.support.R

class ProfileActivity : BaseActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_profile)

        val saveStatus = findViewById<TextView>(R.id.saveStatus)
        findViewById<Button>(R.id.saveProfileButton).setOnClickListener {
            saveStatus.text = "Profile saved"
        }

        wireBottomNav(active = 3)
    }
}
