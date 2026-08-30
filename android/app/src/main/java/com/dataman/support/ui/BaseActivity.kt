package com.dataman.support.ui

import android.content.Context
import android.content.Intent
import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity
import androidx.appcompat.app.AppCompatDelegate
import com.dataman.support.R
import com.google.android.material.bottomnavigation.BottomNavigationView

open class BaseActivity : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val savedMode = getSharedPreferences("hearu_prefs", Context.MODE_PRIVATE)
            .getInt("theme_mode", AppCompatDelegate.MODE_NIGHT_FOLLOW_SYSTEM)
        AppCompatDelegate.setDefaultNightMode(savedMode)
    }

    protected fun setupBottomNavigation(navView: BottomNavigationView) {
        navView.setOnItemSelectedListener { item ->
            val isGiver = getSharedPreferences("hearu_prefs", Context.MODE_PRIVATE).getBoolean("is_giver", false)
            when (item.itemId) {
                R.id.nav_home -> {
                    startActivityWithFlags(Intent(this, if (isGiver) GiverDashboardActivity::class.java else SessionListActivity::class.java))
                    return@setOnItemSelectedListener true
                }
                R.id.nav_chat -> {
                    startActivityWithFlags(Intent(this, if (isGiver) SessionListActivity::class.java else ChatActivity::class.java))
                    return@setOnItemSelectedListener true
                }
                R.id.nav_profile -> {
                    startActivityWithFlags(Intent(this, ProfileActivity::class.java))
                    return@setOnItemSelectedListener true
                }
                R.id.nav_settings -> {
                    startActivityWithFlags(Intent(this, SettingsActivity::class.java))
                    return@setOnItemSelectedListener true
                }
            }
            false
        }
    }

    private fun startActivityWithFlags(intent: Intent) {
        intent.addFlags(Intent.FLAG_ACTIVITY_REORDER_TO_FRONT)
        startActivity(intent)
    }

    protected fun updateNavigationBarState(navView: BottomNavigationView, actionId: Int) {
        navView.menu.findItem(actionId)?.isChecked = true
    }
}
