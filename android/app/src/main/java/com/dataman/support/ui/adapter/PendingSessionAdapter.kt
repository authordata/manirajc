package com.dataman.support.ui.adapter

import android.view.LayoutInflater
import android.view.View
import android.view.ViewGroup
import android.widget.Button
import android.widget.TextView
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView
import com.dataman.support.R
import com.dataman.support.data.model.SessionInfo
import com.google.android.material.chip.Chip

class PendingSessionAdapter(
    private val onAcceptClick: (SessionInfo) -> Unit,
    private val onPassClick: (SessionInfo) -> Unit
) : ListAdapter<SessionInfo, PendingSessionAdapter.PendingSessionViewHolder>(PendingSessionDiffCallback()) {

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): PendingSessionViewHolder {
        val view = LayoutInflater.from(parent.context).inflate(R.layout.item_pending_session, parent, false)
        return PendingSessionViewHolder(view, onAcceptClick, onPassClick)
    }

    override fun onBindViewHolder(holder: PendingSessionViewHolder, position: Int) {
        holder.bind(getItem(position))
    }

    class PendingSessionViewHolder(
        itemView: View,
        private val onAcceptClick: (SessionInfo) -> Unit,
        private val onPassClick: (SessionInfo) -> Unit
    ) : RecyclerView.ViewHolder(itemView) {
        private val textSeekerAlias: TextView = itemView.findViewById(R.id.text_seeker_alias)
        private val chipCause: Chip = itemView.findViewById(R.id.chip_cause)
        private val textTimeAgo: TextView = itemView.findViewById(R.id.text_time_ago)
        private val btnAccept: Button = itemView.findViewById(R.id.btn_accept)
        private val btnPass: Button = itemView.findViewById(R.id.btn_pass)

        fun bind(session: SessionInfo) {
            textSeekerAlias.text = session.seekerAlias ?: "Anonymous"
            chipCause.text = session.cause ?: "General Chat"
            textTimeAgo.text = session.createdAt

            btnAccept.setOnClickListener { onAcceptClick(session) }
            btnPass.setOnClickListener { onPassClick(session) }
        }
    }
}

class PendingSessionDiffCallback : DiffUtil.ItemCallback<SessionInfo>() {
    override fun areItemsTheSame(oldItem: SessionInfo, newItem: SessionInfo): Boolean {
        return oldItem.sessionId == newItem.sessionId
    }

    override fun areContentsTheSame(oldItem: SessionInfo, newItem: SessionInfo): Boolean {
        return oldItem == newItem
    }
}
