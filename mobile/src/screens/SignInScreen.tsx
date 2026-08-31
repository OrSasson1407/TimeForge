import { useState } from 'react'
import {
  ActivityIndicator,
  KeyboardAvoidingView,
  Platform,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native'
import { signInWithEmailAndPassword } from 'firebase/auth'

import { getFirebaseAuth } from '../auth/firebase'

export function SignInScreen() {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [submitting, setSubmitting] = useState(false)

  async function handleSignIn() {
    setError(null)
    setSubmitting(true)
    try {
      await signInWithEmailAndPassword(getFirebaseAuth(), email.trim(), password)
      // No navigation here: App subscribes to auth state and swaps screens,
      // so there is exactly one place that decides what is on screen.
    } catch {
      // Deliberately one message for every failure. Distinguishing "no such
      // account" from "wrong password" would turn this into an account
      // enumeration oracle, exactly as the web app avoids.
      setError('Incorrect email or password.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <KeyboardAvoidingView
      style={styles.container}
      behavior={Platform.OS === 'ios' ? 'padding' : undefined}
    >
      <View style={styles.card}>
        <Text style={styles.title}>TimeForge</Text>
        <Text style={styles.subtitle}>Sign in to see your timetable.</Text>

        {error ? <Text style={styles.error}>{error}</Text> : null}

        <Text style={styles.label}>Email</Text>
        <TextInput
          style={styles.input}
          value={email}
          onChangeText={setEmail}
          autoCapitalize="none"
          autoComplete="email"
          keyboardType="email-address"
          textContentType="emailAddress"
          editable={!submitting}
        />

        <Text style={styles.label}>Password</Text>
        <TextInput
          style={styles.input}
          value={password}
          onChangeText={setPassword}
          secureTextEntry
          autoCapitalize="none"
          textContentType="password"
          editable={!submitting}
        />

        <TouchableOpacity
          style={[styles.button, submitting && styles.buttonDisabled]}
          onPress={handleSignIn}
          disabled={submitting || !email || !password}
          accessibilityRole="button"
          accessibilityLabel="Sign in"
        >
          {submitting ? (
            <ActivityIndicator color="#fff" />
          ) : (
            <Text style={styles.buttonText}>Sign in</Text>
          )}
        </TouchableOpacity>
      </View>
    </KeyboardAvoidingView>
  )
}

const styles = StyleSheet.create({
  container: { flex: 1, justifyContent: 'center', backgroundColor: '#f7f7f8', padding: 20 },
  card: { backgroundColor: '#fff', borderWidth: 1, borderColor: '#e3e3e6', padding: 24 },
  title: { fontSize: 26, fontWeight: '700', color: '#1f1f28' },
  subtitle: { fontSize: 14, color: '#6b6b76', marginTop: 4, marginBottom: 20 },
  label: { fontSize: 12, letterSpacing: 0.6, color: '#6b6b76', marginBottom: 6, marginTop: 12 },
  input: { borderWidth: 1, borderColor: '#d8d8de', paddingHorizontal: 12, paddingVertical: 10, fontSize: 16 },
  button: {
    backgroundColor: '#4338ca',
    paddingVertical: 14,
    alignItems: 'center',
    marginTop: 24,
  },
  buttonDisabled: { opacity: 0.6 },
  buttonText: { color: '#fff', fontWeight: '600', fontSize: 16 },
  error: { color: '#dc2626', marginBottom: 8 },
})
