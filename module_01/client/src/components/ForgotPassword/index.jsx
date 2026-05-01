import { useState } from "react";
import axios from "axios";
import { Link } from "react-router-dom";
import styles from "./styles.module.css";

const ForgotPassword = () => {
    const [email, setEmail] = useState("");
    const [error, setError] = useState("");
    const [message, setMessage] = useState("");
    const [loading, setLoading] = useState(false);

    const handleSubmit = async (e) => {
        e.preventDefault();
        setLoading(true);
        setError("");
        setMessage("");
        try {
            const { data } = await axios.post("http://localhost:8080/api/auth/forgot-password", { email });
            setMessage(data.message);
        } catch (error) {
            setError(error.response?.data?.message || "Something went wrong");
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className={styles.login_container}>
            <div className={styles.forgot_form_container}>
                <form className={styles.form_container} onSubmit={handleSubmit}>
                    <h1>Forgot Password</h1>
                    <p className={styles.subtitle}>Enter your email and we'll send you a reset link</p>
                    <input
                        type="email"
                        placeholder="Enter your email"
                        value={email}
                        onChange={(e) => setEmail(e.target.value)}
                        required
                        className={styles.input}
                    />
                    {error && <div className={styles.error_msg}>{error}</div>}
                    {message && <div className={styles.success_msg}>{message}</div>}
                    <button type="submit" className={styles.green_btn} disabled={loading}>
                        {loading ? "Sending..." : "Send Reset Link"}
                    </button>
                    <Link to="/login" className={styles.back_link}>
                        Back to Login
                    </Link>
                </form>
            </div>
        </div>
    );
};

export default ForgotPassword;