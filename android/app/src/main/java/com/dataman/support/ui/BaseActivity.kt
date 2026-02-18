package com.dataman.support.ui

import android.content.Intent
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity
import com.dataman.support.R

abstract class BaseActivity : AppCompatActivity() {

    protected fun wireBottomNav(active: Int) {
        val home = findViewById<TextView?>(R.id.navHome)
        val chat = findViewById<TextView?>(R.id.navChat)
        val settings = findViewById<TextView?>(R.id.navSettings)
        val profile = findViewById<TextView?>(R.id.navProfile)

        home?.setOnClickListener { startActivity(Intent(this, OnboardingActivity::class.java)) }
        chat?.setOnClickListener { startActivity(Intent(this, ChatActivity::class.java)) }
        settings?.setOnClickListener { startActivity(Intent(this, SettingsActivity::class.java)) }
        profile?.setOnClickListener { startActivity(Intent(this, ProfileActivity::class.java)) }

        listOf(home, chat, settings, profile).forEachIndexed { index, textView ->
            textView?.alpha = if (index == active) 1f else 0.55f
        }
    }
}
