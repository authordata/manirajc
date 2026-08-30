package com.dataman.support.ui

import android.os.Bundle
import android.view.View
import android.widget.ArrayAdapter
import com.dataman.support.R
import com.dataman.support.databinding.ActivityProfileBinding

class ProfileActivity : BaseActivity() {

    private lateinit var binding: ActivityProfileBinding

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityProfileBinding.inflate(layoutInflater)
        setContentView(binding.root)

        setupBottomNavigation(binding.navBottom.bottomNavigationView)
        updateNavigationBarState(binding.navBottom.bottomNavigationView, R.id.nav_profile)

        setupUI()
        setupListeners()
    }

    private fun setupUI() {
        val causes = arrayOf("Anxiety", "Depression", "Stress", "Loneliness")
        binding.spinnerCauses.adapter = ArrayAdapter(this, android.R.layout.simple_spinner_dropdown_item, causes)
        
        binding.etEmail.setText("user@example.com")
        binding.etDisplayName.setText("Anonymous User")
    }

    private fun setupListeners() {
        binding.btnSaveProfile.setOnClickListener {
            showLoading(true)
            binding.progressBar.postDelayed({ showLoading(false) }, 1000)
        }
    }

    private fun showLoading(isLoading: Boolean) {
        binding.progressBar.visibility = if (isLoading) View.VISIBLE else View.GONE
        binding.btnSaveProfile.isEnabled = !isLoading
    }
}
