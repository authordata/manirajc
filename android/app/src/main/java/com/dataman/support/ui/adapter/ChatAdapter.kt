package com.dataman.support.ui.adapter

import android.view.Gravity
import android.view.LayoutInflater
import android.view.ViewGroup
import android.widget.LinearLayout
import androidx.recyclerview.widget.DiffUtil
import androidx.recyclerview.widget.ListAdapter
import androidx.recyclerview.widget.RecyclerView
import com.dataman.support.R
import com.dataman.support.data.model.ChatMessage
import com.dataman.support.databinding.ItemChatMessageBinding

class ChatAdapter : ListAdapter<ChatMessage, ChatAdapter.ChatViewHolder>(MessageDiffCallback()) {

    override fun onCreateViewHolder(parent: ViewGroup, viewType: Int): ChatViewHolder {
        val binding = ItemChatMessageBinding.inflate(
            LayoutInflater.from(parent.context), parent, false
        )
        return ChatViewHolder(binding)
    }

    override fun onBindViewHolder(holder: ChatViewHolder, position: Int) {
        holder.bind(getItem(position))
    }

    inner class ChatViewHolder(private val binding: ItemChatMessageBinding) :
        RecyclerView.ViewHolder(binding.root) {

        fun bind(message: ChatMessage) {
            binding.tvSender.text = message.senderLabel
            binding.tvContent.text = message.content
            binding.tvTimestamp.text = message.createdAt

            val isUser = message.senderLabel.equals("You", ignoreCase = true)

            val params = binding.cardMessage.layoutParams as LinearLayout.LayoutParams
            if (isUser) {
                params.gravity = Gravity.END
                binding.cardMessage.setCardBackgroundColor(
                    binding.root.context.getColor(R.color.chat_user_bubble)
                )
            } else {
                params.gravity = Gravity.START
                binding.cardMessage.setCardBackgroundColor(
                    binding.root.context.getColor(R.color.chat_system_bubble)
                )
            }
            binding.cardMessage.layoutParams = params
        }
    }

    private class MessageDiffCallback : DiffUtil.ItemCallback<ChatMessage>() {
        override fun areItemsTheSame(oldItem: ChatMessage, newItem: ChatMessage): Boolean {
            return oldItem.id == newItem.id
        }

        override fun areContentsTheSame(oldItem: ChatMessage, newItem: ChatMessage): Boolean {
            return oldItem == newItem
        }
    }
}
