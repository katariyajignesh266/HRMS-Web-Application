import { getApps, initializeApp } from "firebase/app"
import { getAuth, onAuthStateChanged, signInWithEmailAndPassword, signOut } from "firebase/auth"
import { call } from "frappe-ui"

let authPromise

async function getFirebaseAuth() {
	if (!authPromise) {
		authPromise = call("hrms.api.firebase_auth.firebase_config")
			.then((response) => {
				const config = response?.configured ? response : (response?.message || {})
				if (!config?.configured) {
					throw new Error("Firebase Web Authentication is not configured.")
				}
				const app = getApps()[0] || initializeApp({
					apiKey: config.api_key,
					authDomain: config.auth_domain,
					projectId: config.project_id,
					appId: config.app_id,
				})
				return getAuth(app)
			})
			.catch((err) => {
				authPromise = null
				throw err
			})
	}
	return authPromise
}

export async function firebaseLogin(email, password) {
	const auth = await getFirebaseAuth()
	const credential = await signInWithEmailAndPassword(auth, email, password)
	return credential.user.getIdToken(true)
}

export async function restoreFirebaseUser() {
	try {
		const auth = await getFirebaseAuth()
		return await new Promise((resolve) => {
			const unsubscribe = onAuthStateChanged(auth, (user) => {
				unsubscribe()
				resolve(user)
			})
		})
	} catch {
		return null
	}
}

export async function firebaseLogout() {
	try {
		const auth = await getFirebaseAuth()
		await signOut(auth)
	} catch {
		// Firebase may be unconfigured while the Frappe session still needs clearing.
	}
}