import jenkins.model.*

def job_name = "jcasc-dsl"

if (Jenkins.instance.getItem(job_name)) {
	println("Start jcasc init!")
	Jenkins.instance.getItem(job_name).scheduleBuild(5)
} else {
	println("jcasc job doesn't exist")
}
