package com.dataman.support.ui

import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.view.View
import android.widget.TextView
import androidx.appcompat.app.AlertDialog
import androidx.recyclerview.widget.LinearLayoutManager
import androidx.recyclerview.widget.RecyclerView
import com.dataman.support.R
import com.dataman.support.data.model.SessionInfo
import com.dataman.support.ui.adapter.SessionAdapter
import com.google.android.material.floatingactionbutton.FloatingActionButton
import com.google.android.material.bottomnavigation.BottomNavigationView
import kotlinx.coroutines.*

class SessionListActivity : BaseActivity() {

    private lateinit var recyclerView: RecyclerView
    private lateinit var emptyStateText: TextView
    private lateinit var fabNewSession: FloatingActionButton
    private lateinit var adapter: SessionAdapter
    private var pollJob: Job? = null

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_session_list)

        val navView = findViewById<BottomNavigationView>(R.id.bottom_navigation)
        setupBottomNavigation(navView)
        val isGiver = getSharedPreferences("hearu_prefs", Context.MODE_PRIVATE).getBoolean("is_giver", false)
        updateNavigationBarState(navView, if(isGiver) R.id.nav_chat else R.id.nav_home)

        recyclerView = findViewById(R.id.recycler_sessions)
        emptyStateText = findViewById(R.id.text_empty_state)
        fabNewSession = findViewById(R.id.fab_new_session)

        adapter = SessionAdapter { session ->
            val intent = Intent(this, ChatActivity::class.java)
            intent.putExtra("session_id", session.sessionId)
            startActivity(intent)
        }
        recyclerView.layoutManager = LinearLayoutManager(this)
        recyclerView.adapter = adapter

        if (isGiver) {
            fabNewSession.visibility = View.GONE
        } else {
            fabNewSession.setOnClickListener {
                showSupportTypeDialog()
            }
        }
    }

    override fun onResume() {
        super.onResume()
        startPolling()
    }

    override fun onPause() {
        super.onPause()
        pollJob?.cancel()
    }

    private fun startPolling() {
        pollJob = CoroutineScope(Dispatchers.Main).launch {
            while (isActive) {
                fetchSessions()
                delay(10000)
            }
        }
    }

    private fun fetchSessions() {
        // Mocking API call logic for now since we don't have Retrofit instance here directly
        // In a real app, inject ApiService and call getActiveSessions
    }

    private fun showSupportTypeDialog() {
        val options = arrayOf(getString(R.string.ai_support), getString(R.string.human_support))
        AlertDialog.Builder(this)
            .setTitle(R.string.choose_support)
            .setItems(options) { _, which ->
                // Handle choice
            }
            .show()
    }
}
