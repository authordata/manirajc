package com.dataman.support.ui
import android.content.Intent
import android.os.Bundle
import android.os.CountDownTimer
import androidx.activity.viewModels
import androidx.appcompat.app.AppCompatActivity
import com.dataman.support.databinding.ActivityOtpVerificationBinding
import com.dataman.support.ui.viewmodel.AuthViewModel
import com.dataman.support.ui.viewmodel.ViewModelFactory
import com.google.android.material.snackbar.Snackbar
class OtpVerificationActivity : AppCompatActivity() {
private lateinit var binding: ActivityOtpVerificationBinding
private val authViewModel: AuthViewModel by viewModels { ViewModelFactory(applicationContext) }
private var timer: CountDownTimer? = null
override fun onCreate(savedInstanceState: Bundle?) {
super.onCreate(savedInstanceState)
binding = ActivityOtpVerificationBinding.inflate(layoutInflater)
setContentView(binding.root)
setupListeners()
startResendTimer()
}
private fun setupListeners() {
binding.btnVerify.setOnClickListener {
val code = binding.etOtpCode.text.toString()
if (code.length == 6) {
navigateToChat() 
} else {
Snackbar.make(binding.root, "Enter 6-digit code", Snackbar.LENGTH_SHORT).show()
}
}
binding.btnResend.setOnClickListener {
startResendTimer()
Snackbar.make(binding.root, "Code resent", Snackbar.LENGTH_SHORT).show()
}
}
private fun startResendTimer() {
binding.btnResend.isEnabled = false
timer?.cancel()
timer = object : CountDownTimer(59000, 1000) {
override fun onTick(millisUntilFinished: Long) {
val seconds = millisUntilFinished / 1000
binding.tvTimer.text = String.format("00:%02d", seconds)
}
override fun onFinish() {
binding.btnResend.isEnabled = true
binding.tvTimer.text = "00:00"
}
}.start()
}
private fun navigateToChat() {
startActivity(Intent(this, ChatActivity::class.java))
finishAffinity()
}
override fun onDestroy() {
super.onDestroy()
timer?.cancel()
}
}