import { computed, reactive } from "vue"
import { createResource, call } from "frappe-ui"
import { userResource } from "./user"
import { employeeResource } from "./employee"
import router from "@/router"
import { firebaseLogin, firebaseLogout, restoreFirebaseUser } from "./firebase"

export function sessionUser() {
	let cookies = new URLSearchParams(document.cookie.split("; ").join("&"))
	let _sessionUser = cookies.get("user_id")
	if (_sessionUser === "Guest") {
		_sessionUser = null
	}
	return _sessionUser
}

function handleLogin(response, redirect = true) {
	if (response?.message === "Logged In" || response === "Logged In") {
		userResource.reload()
		employeeResource.reload()

		session.user = sessionUser()
		if (redirect) router.replace({ path: "/" })
	}
}

export const session = reactive({
	login: async (email, password) => {
		try {
			const idToken = await firebaseLogin(email, password)
			const response = await call("hrms.api.firebase_auth.login_with_firebase_token", { id_token: idToken })
			handleLogin(response)
			return response
		} catch (fbError) {
			try {
				const response = await call("login", { usr: email, pwd: password })
				handleLogin(response)
				return response
			} catch {
				throw fbError
			}
		}
	},
	restore: async () => {
		if (sessionUser()) return
		const user = await restoreFirebaseUser()
		if (!user) return
		const idToken = await user.getIdToken()
		const response = await call("hrms.api.firebase_auth.login_with_firebase_token", { id_token: idToken })
		handleLogin(response, false)
	},
	otp: async (tmp_id, otp) => {
		const response = await call("login", { tmp_id, otp })
		handleLogin(response)
		return response
	},
	logout: createResource({
		url: "logout",
		method: "POST",
		async onSuccess() {
			await firebaseLogout()
			userResource.reset()
			employeeResource.reset()

			session.user = sessionUser()
			router.replace({ name: "Login" })
			window.location.reload()
		},
		async onError() {
			await firebaseLogout()
			userResource.reset()
			employeeResource.reset()
			session.user = null
			router.replace({ name: "Login" })
		},
	}),
	user: sessionUser(),
	isLoggedIn: computed(() => !!session.user),
})
