package com.dataman.support.ui

import android.content.Intent
import android.os.Bundle
import android.view.animation.AlphaAnimation
import androidx.appcompat.app.AppCompatActivity
import com.dataman.support.databinding.ActivityOnboardingBinding

class OnboardingActivity : AppCompatActivity() {

    private lateinit var binding: ActivityOnboardingBinding

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        // Mock TokenManager check
        // if (TokenManager.isLoggedIn()) {
        //     startActivity(Intent(this, ChatActivity::class.java))
        //     finish()
        //     return
        // }

        binding = ActivityOnboardingBinding.inflate(layoutInflater)
        setContentView(binding.root)

        animateElements()

        binding.btnGetStarted.setOnClickListener {
            startActivity(Intent(this, AuthActivity::class.java))
        }
    }

    private fun animateElements() {
        val fadeIn = AlphaAnimation(0f, 1f).apply {
            duration = 1000
            fillAfter = true
        }
        binding.tvHeart.startAnimation(fadeIn)
        binding.tvTitle.startAnimation(fadeIn)
        binding.tvSubtitle.startAnimation(fadeIn)
    }
}
