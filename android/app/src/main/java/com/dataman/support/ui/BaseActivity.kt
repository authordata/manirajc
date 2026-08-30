package com.dataman.support.ui

import android.content.Intent
import android.os.Bundle
import androidx.appcompat.app.AppCompatActivity
import com.google.android.material.bottomnavigation.BottomNavigationView
import com.dataman.support.R

open class BaseActivity : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
    }

    protected fun setupBottomNavigation(navView: BottomNavigationView) {
        navView.setOnItemSelectedListener { item ->
            when (item.itemId) {
                R.id.nav_home -> {
                    return@setOnItemSelectedListener true
                }
                R.id.nav_chat -> {
                    startActivityWithFlags(Intent(this, ChatActivity::class.java))
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
