package com.dataman.support.ui

import android.content.Context
import android.content.Intent
import android.os.Bundle
import android.widget.Button
import android.widget.RadioGroup
import android.widget.Toast
import android.widget.ViewFlipper
import androidx.appcompat.app.AppCompatActivity
import com.dataman.support.R

class GiverOnboardingActivity : AppCompatActivity() {

    private lateinit var viewFlipper: ViewFlipper

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_giver_onboarding)

        viewFlipper = findViewById(R.id.viewFlipper)

        findViewById<Button>(R.id.btnNext1).setOnClickListener { viewFlipper.showNext() }
        
        findViewById<Button>(R.id.btnNext2).setOnClickListener { viewFlipper.showNext() }
        findViewById<Button>(R.id.btnPrev2).setOnClickListener { viewFlipper.showPrevious() }

        findViewById<Button>(R.id.btnNext3).setOnClickListener { viewFlipper.showNext() }
        findViewById<Button>(R.id.btnPrev3).setOnClickListener { viewFlipper.showPrevious() }

        findViewById<Button>(R.id.btnSubmitQuiz).setOnClickListener {
            checkQuizAndFinish()
        }
        findViewById<Button>(R.id.btnPrev4).setOnClickListener { viewFlipper.showPrevious() }
    }

    private fun checkQuizAndFinish() {
        val q1 = findViewById<RadioGroup>(R.id.rgQ1).checkedRadioButtonId
        val q2 = findViewById<RadioGroup>(R.id.rgQ2).checkedRadioButtonId
        val q3 = findViewById<RadioGroup>(R.id.rgQ3).checkedRadioButtonId

        if (q1 == R.id.rbQ1B && q2 == R.id.rbQ2B && q3 == R.id.rbQ3B) {
            val prefs = getSharedPreferences("hearu_prefs", Context.MODE_PRIVATE)
            prefs.edit().putBoolean("giver_trained", true).apply()
            
            Toast.makeText(this, getString(R.string.quiz_passed), Toast.LENGTH_LONG).show()
            startActivity(Intent(this, GiverDashboardActivity::class.java))
            finish()
        } else {
            Toast.makeText(this, getString(R.string.quiz_failed), Toast.LENGTH_LONG).show()
            viewFlipper.displayedChild = 1
        }
    }
}