import { useState } from "react";
import axios from "axios";
import { useLocation } from "react-router-dom";
import styles from "./styles.module.css";

const VerifyOTP = () => {
    const [otp, setOtp] = useState("");
    const [error, setError] = useState("");
    const [message, setMessage] = useState("");
    const [loading, setLoading] = useState(false);
    const location = useLocation();
    const email = location.state?.email;

    const handleSubmit = async (e) => {
        e.preventDefault();
        try {
            const response = await axios.post("http://localhost:8080/api/user/verify-otp", { email, otp }); 
            localStorage.setItem("token", response.data.data);
            window.location.href = "/";
        } catch (error) {
            setError(error.response?.data?.message || "Verification failed");
        }
    };

    const handleResendOTP = async () => {
        setLoading(true);
        setError("");
        setMessage("");
        try {
            await axios.post("http://localhost:8080/api/user/resend-otp", { email });
            setMessage("New OTP sent to your email");
        } catch (error) {
            setError(error.response?.data?.message || "Failed to resend OTP");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className={styles.verify_container}>
            <div className={styles.verify_form_container}>
                <form className={styles.form_container} onSubmit={handleSubmit}>
                    <h1>Verify OTP</h1>
                    <h2>Enter OTP sent to {email}</h2>
                    <input
                        type="text"
                        placeholder="Enter OTP"
                        value={otp}
                        onChange={(e) => setOtp(e.target.value)}
                        required
                        className={styles.input}
                    />
                    {error && <div className={styles.error_msg}>{error}</div>}
                    {message && <div className={styles.success_msg}>{message}</div>}
                    <button type="submit" className={styles.green_btn}>
                        Verify
                    </button>
                    <button
                        type="button"
                        className={styles.resend_btn}
                        onClick={handleResendOTP}
                        disabled={loading}
                    >
                        {loading ? "Sending..." : "Resend OTP"}
                    </button>
                </form>
            </div>
        </div>
    );
};

export default VerifyOTP;