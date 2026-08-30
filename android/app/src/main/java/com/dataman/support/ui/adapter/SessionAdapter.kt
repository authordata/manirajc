package com.dataman.support.ui.adapter

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.TextView
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView
import com.dataman.support.R
import com.dataman.support.data.model.SessionInfo
import com.google.android.material.chip.Chip

class SessionAdapter(private val onSessionClick: (SessionInfo) -> Unit) :
    ListAdapter<SessionInfo, SessionAdapter.SessionViewHolder>(SessionDiffCallback()) {

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): SessionViewHolder {
        val view = LayoutInflater.from(parent.context).inflate(R.layout.item_session, parent, false)
        return SessionViewHolder(view, onSessionClick)
    }

    override fun onBindViewHolder(holder: SessionViewHolder, position: Int) {
        holder.bind(getItem(position))
    }

    class SessionViewHolder(itemView: View, val onSessionClick: (SessionInfo) -> Unit) : RecyclerView.ViewHolder(itemView) {
        private val textCause: TextView = itemView.findViewById(R.id.text_cause)
        private val chipStatus: Chip = itemView.findViewById(R.id.chip_status)
        private val textLastMessage: TextView = itemView.findViewById(R.id.text_last_message)
        private val textTime: TextView = itemView.findViewById(R.id.text_time)
        private val textTypeIndicator: TextView = itemView.findViewById(R.id.text_type_indicator)

        fun bind(session: SessionInfo) {
            textCause.text = session.cause ?: "General Chat"
            chipStatus.text = session.status
            when (session.status.uppercase()) {
                "ACTIVE" -> chipStatus.setChipBackgroundColorResource(android.R.color.holo_green_light)
                "OPEN" -> chipStatus.setChipBackgroundColorResource(android.R.color.holo_orange_light)
                "CLOSED" -> chipStatus.setChipBackgroundColorResource(android.R.color.darker_gray)
            }
            textLastMessage.text = session.lastMessage ?: ""
            textTime.text = session.lastMessageTime ?: session.createdAt
            textTypeIndicator.text = if (session.isAiSession) "🤖 AI Support" else "👤 Human Support"

            itemView.setOnClickListener { onSessionClick(session) }
        }
    }
}

class SessionDiffCallback : DiffUtil.ItemCallback<SessionInfo>() {
    override fun areItemsTheSame(oldItem: SessionInfo, newItem: SessionInfo): Boolean {
        return oldItem.sessionId == newItem.sessionId
    }

    override fun areContentsTheSame(oldItem: SessionInfo, newItem: SessionInfo): Boolean {
        return oldItem == newItem
    }
}
