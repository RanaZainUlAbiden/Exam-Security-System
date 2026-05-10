const nodemailer = require('nodemailer');

const transporter = nodemailer.createTransport({
    service: 'gmail',
    auth: { user: process.env.EMAIL_USER, pass: process.env.EMAIL_PASS }
});

const sendOTP = async (email, otp) => {
    await transporter.sendMail({
        to: email,
        subject: 'Verify Your Email - Online Examination System',
        html: `
            <h2>Online Examination System</h2>
            <p>Dear User,</p>
            <p>Thank you for registering with our Online Examination System.</p>
            <p>Your OTP is: <strong>${otp}</strong></p>
            <p>Valid for 5 minutes</p>
            <p>This OTP is required to complete your registration.</p>
            <p><strong>Security Alert:</strong> If you did not request this, please ignore this email. Do not share this OTP with anyone.</p>
            <hr>
            <p>&copy; 2024 Online Examination System. All rights reserved.</p>
        `
    });
};

const sendResetEmail = async (email, resetLink) => {
    await transporter.sendMail({
        to: email,
        subject: 'Password Reset - Online Examination System',
        html: `
            <h2>Online Examination System</h2>
            <p>Dear User,</p>
            <p>We received a request to reset your password.</p>
            <p>Click the button below to reset your password:</p>
            <a href="${resetLink}" style="
                display: inline-block;
                padding: 12px 24px;
                background-color: #3bb19b;
                color: white;
                text-decoration: none;
                border-radius: 5px;
                font-weight: bold;
                margin: 10px 0;
            ">Reset Password</a>
            <p>This link is valid for <strong>1 hour</strong>.</p>
            <p><strong>Security Alert:</strong> If you did not request this, please ignore this email.</p>
            <hr>
            <p>&copy; 2024 Online Examination System. All rights reserved.</p>
        `
    });
};

const generateOTP = () => Math.floor(100000 + Math.random() * 900000).toString();

module.exports = { sendOTP, sendResetEmail, generateOTP };