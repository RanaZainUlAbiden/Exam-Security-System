import { useState } from "react";
import axios from "axios";
import { Link, useNavigate } from "react-router-dom";
import styles from "./styles.module.css";
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import { faEye, faEyeSlash } from '@fortawesome/free-solid-svg-icons';

const Signup = () => {
	const [data, setData] = useState({
		firstName: "",
		lastName: "",
		email: "",
		password: "",
		role: "",
	});
	const [error, setError] = useState("");
	const [showPassword, setShowPassword] = useState(false);
	const [loading, setLoading] = useState(false);
	const navigate = useNavigate();

	const handleChange = ({ currentTarget: input }) => {
		setData({ ...data, [input.name]: input.value });
	};

	const handleSubmit = async (e) => {
		e.preventDefault();
		setLoading(true);
		try {
			const url = "http://localhost:8080/api/user";
			const response = await axios.post(url, data);
			navigate("/verify-otp", { state: { email: response.data.email } });
		} catch (error) {
			if (error.response && error.response.status >= 400 && error.response.status <= 500) {
				setError(error.response.data.message);
			}
		} finally {
			setLoading(false);
		}
	};

	return (
		<div className={styles.signup_container}>
			<div className={styles.signup_form_container}>
				<div className={styles.left}>
					<h1>Welcome Back</h1>
					<Link to="/login">
						<button type="button" className={styles.white_btn}>
							Sing in
						</button>
					</Link>
				</div>
				<div className={styles.right}>
					<form className={styles.form_container} onSubmit={handleSubmit}>
						<h1>Create Account</h1>
						<input
							type="text"
							placeholder="First Name"
							name="firstName"
							onChange={handleChange}
							value={data.firstName}
							required
							className={styles.input}
						/>
						<input
							type="text"
							placeholder="Last Name"
							name="lastName"
							onChange={handleChange}
							value={data.lastName}
							required
							className={styles.input}
						/>
						<select
							name="role"
							onChange={handleChange}
							value={data.role}
							required
							className={styles.input}
							style={{ cursor: "pointer" }}
						>
							<option value="" disabled>Select Role</option>
							<option value="Student">Student</option>
							<option value="Examiner">Examiner</option>
						</select>
						<input
							type="email"
							placeholder="Email"
							pattern="[a-zA-Z0-9._%+\-]+@gmail\.com"
							title="Please enter a valid Gmail address (@gmail.com)"
							name="email"
							onChange={handleChange}
							value={data.email}
							required
							className={styles.input}
						/>
						<div className={styles.password_container}>
							<input
								type={showPassword ? "text" : "password"}
								placeholder='Password'
								name='password'
								onChange={handleChange}
								value={data.password}
								required
								className={styles.input}
							/>
							<button
								type="button"
								className={styles.toggle_btn}
								onClick={() => setShowPassword(!showPassword)}
							>
								<FontAwesomeIcon icon={showPassword ? faEye : faEyeSlash} />
							</button>
						</div>
						{error && <div className={styles.error_msg}>{error}</div>}
						<button type="submit" className={styles.green_btn} disabled={loading}>
							{loading ? "Sending OTP..." : "Sign Up"}
						</button>
						<Link to="/login" className={styles.mobile_signin}>
							<button type="button" className={styles.white_btn}>
								Sign In
							</button>
						</Link>
					</form>
				</div>
			</div>
		</div>
	);
};

export default Signup;