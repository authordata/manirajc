package com.dataman.support

import android.os.Bundle
import android.widget.Button
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity

class DashboardActivity : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_dashboard)

        val statusText = findViewById<TextView>(R.id.statusText)
        val humanBtn = findViewById<Button>(R.id.humanSupportBtn)
        val aiBtn = findViewById<Button>(R.id.aiSupportBtn)

        humanBtn.setOnClickListener {
            statusText.text = "Human support request queued (API integration pending)."
        }

        aiBtn.setOnClickListener {
            statusText.text = "AI support session started (API integration pending)."
        }
    }
}
