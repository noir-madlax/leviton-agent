"use client"

import { useState } from 'react'
import { supabase } from '@/lib/supabase'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'

export default function TestConfigPage() {
  const [testResults, setTestResults] = useState<any>({})
  const [loading, setLoading] = useState(false)

  const runTests = async () => {
    setLoading(true)
    const results: any = {}

    // Test 1: Environment variables
    results.envVars = {
      supabaseUrl: process.env.NEXT_PUBLIC_SUPABASE_URL || 'Not set',
      supabaseAnonKey: process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY ? 'Set' : 'Not set',
      backendUrl: process.env.NEXT_PUBLIC_BACKEND_URL || 'Not set',
    }

    // Test 2: Supabase connection
    try {
      const { data, error } = await supabase.from('projects').select('count', { count: 'exact', head: true })
      if (error) {
        results.supabaseConnection = { success: false, error: error.message }
      } else {
        results.supabaseConnection = { success: true, count: data?.length || 0 }
      }
    } catch (err) {
      results.supabaseConnection = { success: false, error: String(err) }
    }

    // Test 3: Projects table access
    try {
      const { data, error } = await supabase
        .from('projects')
        .select('id, project_name, status')
        .limit(3)
      
      if (error) {
        results.projectsAccess = { success: false, error: error.message }
      } else {
        results.projectsAccess = { success: true, projects: data }
      }
    } catch (err) {
      results.projectsAccess = { success: false, error: String(err) }
    }

    // Test 4: Backend API
    try {
      const API_BASE_URL = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
      const response = await fetch(`${API_BASE_URL}/api/v1/projects/`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      })
      
      if (response.ok) {
        const data = await response.json()
        results.backendApi = { success: true, projectCount: data.length }
      } else {
        results.backendApi = { success: false, error: `HTTP ${response.status}` }
      }
    } catch (err) {
      results.backendApi = { success: false, error: String(err) }
    }

    setTestResults(results)
    setLoading(false)
  }

  return (
    <div className="container mx-auto p-4 max-w-4xl">
      <h1 className="text-2xl font-bold mb-6">Configuration Test</h1>
      
      <Button onClick={runTests} disabled={loading} className="mb-6">
        {loading ? 'Running Tests...' : 'Run Configuration Tests'}
      </Button>

      {Object.keys(testResults).length > 0 && (
        <div className="space-y-4">
          <Card>
            <CardHeader>
              <CardTitle>Environment Variables</CardTitle>
            </CardHeader>
            <CardContent>
              <pre className="text-sm">{JSON.stringify(testResults.envVars, null, 2)}</pre>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Supabase Connection</CardTitle>
            </CardHeader>
            <CardContent>
              <pre className="text-sm">{JSON.stringify(testResults.supabaseConnection, null, 2)}</pre>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Projects Table Access</CardTitle>
            </CardHeader>
            <CardContent>
              <pre className="text-sm">{JSON.stringify(testResults.projectsAccess, null, 2)}</pre>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Backend API</CardTitle>
            </CardHeader>
            <CardContent>
              <pre className="text-sm">{JSON.stringify(testResults.backendApi, null, 2)}</pre>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
} 