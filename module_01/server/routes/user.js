const router = require("express").Router();
const { User, validate } = require("../models/user")
const bcrypt = require("bcrypt")
const { sendOTP, generateOTP } = require('../otpService');

router.post("/", async (req, res) => {
    try {
        const { error } = validate(req.body);
        if (error)
            return res.status(400).send({ message: error.details[0].message });

        if (req.body.role && !['Examiner', 'Student'].includes(req.body.role)) {
            return res.status(400).send({ message: "Role must be Examiner or Student" })
        }

        const user = await User.findOne({ email: req.body.email });
        if (user)
            return res.status(409).send({ message: "User with given email already exists" });

        const salt = await bcrypt.genSalt(Number(process.env.SALT));
        const hashPassword = await bcrypt.hash(req.body.password, salt);

        const otp = generateOTP();
        const otpExpiry = new Date();
        otpExpiry.setMinutes(otpExpiry.getMinutes() + 5);

        await new User({ ...req.body, password: hashPassword, otp: otp, isVerified: false, otpExpiry: otpExpiry }).save();
        await sendOTP(req.body.email, otp);

        res.status(201).send({ message: "OTP sent to email", email: req.body.email });
    } catch (error) {
        res.status(500).send({ message: "Internal Server Error" })
    }
});

router.post("/verify-otp", async (req, res) => {
    try {
        const { email, otp } = req.body;
        const user = await User.findOne({ email: email, otp: otp });

        if (!user) return res.status(400).send({ message: "Invalid OTP" });

        if (new Date() > user.otpExpiry) {
            return res.status(400).send({ message: "OTP has expired. Request a new one." });
        }

        user.isVerified = true;
        user.otp = undefined;
        user.otpExpiry = undefined;
        await user.save();

        const token = user.generateAuthToken(); 
        res.status(200).send({ message: "Email verified successfully" , data: token });
    } catch (error) {
        res.status(500).send({ message: "Internal Server Error" });
    }
});

router.post("/resend-otp", async (req, res) => {
    try {
        const { email } = req.body;
        const { sendOTP, generateOTP } = require('../otpService');

        const otp = generateOTP();
        const otpExpiry = new Date();
        otpExpiry.setMinutes(otpExpiry.getMinutes() + 10);

        const user = await User.findOne({ email: email });
        if (!user) return res.status(404).send({ message: "User not found" });

        user.otp = otp;
        user.otpExpiry = otpExpiry;
        await user.save();
        await sendOTP(email, otp);

        res.status(200).send({ message: "OTP resent successfully" });
    } catch (error) {
        res.status(500).send({ message: "Internal Server Error" });
    }
});

module.exports = router;