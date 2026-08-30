package com.dataman.support.ui

import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.view.View
import android.widget.TextView
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.dataman.support.R
import com.dataman.support.data.model.SessionInfo
import com.dataman.support.ui.adapter.PendingSessionAdapter
import com.google.android.material.bottomnavigation.BottomNavigationView
import com.google.android.material.materialswitch.MaterialSwitch
import kotlinx.coroutines.*

class GiverDashboardActivity : BaseActivity() {

    private lateinit var recyclerView: RecyclerView
    private lateinit var emptyStateText: TextView
    private lateinit var switchAvailability: MaterialSwitch
    private lateinit var adapter: PendingSessionAdapter
    private var pollJob: Job? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        val prefs = getSharedPreferences("hearu_prefs", Context.MODE_PRIVATE)
        if (!prefs.getBoolean("giver_trained", false)) {
            startActivity(Intent(this, GiverOnboardingActivity::class.java))
            finish()
            return
        }

        setContentView(R.layout.activity_giver_dashboard)

        val navView = findViewById<BottomNavigationView>(R.id.bottom_navigation)
        setupBottomNavigation(navView)
        updateNavigationBarState(navView, R.id.nav_home)

        recyclerView = findViewById(R.id.recycler_pending_sessions)
        emptyStateText = findViewById(R.id.text_empty_state)
        switchAvailability = findViewById(R.id.switch_availability)

        adapter = PendingSessionAdapter(
            onAcceptClick = { session ->
                // Handle accept
                val intent = Intent(this, ChatActivity::class.java)
                intent.putExtra("session_id", session.sessionId)
                startActivity(intent)
            },
            onPassClick = { session ->
                // Handle pass
            }
        )
        recyclerView.layoutManager = LinearLayoutManager(this)
        recyclerView.adapter = adapter

        switchAvailability.setOnCheckedChangeListener { _, isChecked ->
            switchAvailability.text = getString(R.string.you_are) + " " + if (isChecked) getString(R.string.online) else getString(R.string.offline)
            // Call API to toggle
        }
    }

    override fun onResume() {
        super.onResume()
        if (getSharedPreferences("hearu_prefs", Context.MODE_PRIVATE).getBoolean("giver_trained", false)) {
            startPolling()
        }
    }

    override fun onPause() {
        super.onPause()
        pollJob?.cancel()
    }

    private fun startPolling() {
        pollJob = CoroutineScope(Dispatchers.Main).launch {
            while (isActive) {
                fetchPendingSessions()
                delay(5000)
            }
        }
    }

    private fun fetchPendingSessions() {
        // Call API
    }
}