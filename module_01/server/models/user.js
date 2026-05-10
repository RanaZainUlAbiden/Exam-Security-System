const mongoose = require('mongoose');
const jwt = require('jsonwebtoken')
const joi = require('joi');
const passwordComplexity = require('joi-password-complexity');


const  userSchema = new mongoose.Schema({
    firstName: {type: String, required: true},
    lastName: {type: String, required: true},
    email: {type: String, required: true , unique: true},
    password: {type: String, required: true},
    role : {type: String, enum: ['Examiner','Student'], required : true, default: 'Student'},
    isVerified: {type: Boolean, default: false},
    otp: {type: String},
    otpExpiry: {type: Date},
    resetToken: {type: String},        
    resetTokenExpiry: {type: Date}  
});

userSchema.methods.generateAuthToken = function() {
    const token = jwt.sign({_id:this._id /* , role: this.role */},process.env.JWTPRIVATEKEY, {expiresIn: "7d"});
    return token
};

const User = mongoose.model("user", userSchema);

const validate = (data) => {
    const schema = joi.object({
    firstName: joi.string().required().label("FirstName"),
    lastName: joi.string().required().label("LastName"),
    email: joi.string().required().label("Email"),
    password: passwordComplexity().required().label("Password"),
    role: joi.string().valid('Examiner','Student').required().label("Role")
    });
    return schema.validate(data)
}

module.exports = {User, validate};