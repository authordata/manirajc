package com.dataman.support.ui

import android.os.Bundle
import android.widget.Button
import android.widget.EditText
import android.widget.TextView
import com.dataman.support.R

class ChatActivity : BaseActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_chat)

        val transcript = findViewById<TextView>(R.id.chatTranscript)
        val input = findViewById<EditText>(R.id.chatInput)

        findViewById<Button>(R.id.humanSupportBtn).setOnClickListener {
            transcript.append("\n[System] Looking for an available support giver...")
        }

        findViewById<Button>(R.id.aiSupportBtn).setOnClickListener {
            transcript.append("\n[System] HearU AI is ready.")
        }

        findViewById<Button>(R.id.sendButton).setOnClickListener {
            val message = input.text.toString().trim()
            if (message.isNotEmpty()) {
                transcript.append("\nYou: $message")
                transcript.append("\nHearU AI: I hear you. Let us take this one step at a time.")
                input.text.clear()
            }
        }

        wireBottomNav(active = 1)
    }
}
