class AdminIffcoView(AdminLoginRequiredMixin, View):

    def get(self, request):
        courseId = request.GET.get('searchedCourseId', None)
        studentId = request.GET.get('useridsearched', None)

        
        allUserCourses = None

        if courseId and studentId:
            allUserCourses = UserCourse.objects.filter(
                Q(course_id=int(courseId)) & Q(user_id=int(studentId)) &
                Q(course__is_mentorship_program=False)
            ).order_by('-enrolment_created_at')
        elif courseId and not studentId:
            allUserCourses = UserCourse.objects.filter(
                Q(course_id=int(courseId)) &
                Q(course__is_mentorship_program=False)
            ).order_by('-enrolment_created_at')
        elif studentId and not courseId:
            allUserCourses = UserCourse.objects.filter(
                Q(user_id=int(studentId)) &
                Q(course__is_mentorship_program=False)
            ).order_by('-enrolment_created_at')
        else:
            allUserCourses = UserCourse.objects.filter(
                Q(enterprise_academic__isnull=True) &
                Q(course__is_mentorship_program=False)
            ).order_by('-enrolment_created_at')[:200]

        

        enrolled_count = allUserCourses.count()

        # Pagination
        try:
            page = request.GET.get('page', 1)
        except PageNotAnInteger:
            page = 1

        p = Paginator(allUserCourses, 30)
        user_courses_all = p.page(page)

        after_search = False

        # Calculate total assignments if courseId is provided
        total_assignments = 0
        if courseId:
            courseobj = Course.objects.get(id=courseId)
            instructor_batch_ids = SaveCourse.objects.filter(course_id=courseId).values_list('batch_id', flat=True).distinct()
            all_batches = Batch.objects.filter(course_id=courseId, id__in=instructor_batch_ids)
            current_batch = all_batches.filter(batch_active='Y').first() or all_batches.order_by("-add_time").first()

            if current_batch:
                batch_sessions = BatchSession.objects.filter(course=courseobj, batch=current_batch).order_by('session_date')
                for batch in batch_sessions:
                    batch_assignments = batch.get_all_assignment()
                    if batch_assignments:
                        total_assignments += batch_assignments.count()

        return render(request, 'admin_iffco.html', {
            'userCourses': user_courses_all,
            "After_search": after_search,
            "TotalEnrollmentsCount": enrolled_count,
            "TotalAssignments": total_assignments,
            
        })

    def post(self, request):
        courseId = request.POST.get('SelectedCourseId', None)
        batchId = request.POST.get('selectedBatchId', None)
        studentId = request.POST.get('selectedStudentid', None)
        ispaidenroll = request.POST.get('enrolltype', None)
        is_kid = request.POST.get("is_kid")

        if ispaidenroll == '0':
            ispaidenroll = False
        elif ispaidenroll == '1':
            ispaidenroll = True

        user_profile = UserProfile.objects.get(id=int(studentId))
        course = Course.objects.get(id=int(courseId))
        batch = Batch.objects.get(id=int(batchId))

        if UserCourse.objects.filter(Q(course=course) & Q(user=user_profile) & Q(batch=batch)):
            messages.error(request, "Student is already enrolled in this course. Cannot enroll again.")
            return HttpResponseRedirect('/yoshimitsujpinfy/admin_iffco/')

        usercourse_obj = enroll_student(user_profile, course, batch, ispaidenroll)

        if is_kid == 'on':
            text_subject = "Infyni Kids | " + usercourse_obj.course.name + " | Enrollment"
            user_email = request.user.email
            user_email_template = 'email-template-kids-enrollment-confirmation-admin-bulk.html'
            send_mail_register_enrolled_from_icms(user_email, user_profile, usercourse_obj, text_subject, user_email_template, HOST_KID_URL)
        else:
            learner_email_task = LearnerEmailNotification(usercourse_obj.user)
            event_code = EventTypeList.COURSE_ENROLLMENT
            event_type = None
            if event_code:
                event_type_obj = get_event_type(event_code)
                if event_type_obj:
                    event_type = event_type_obj.id

            object_id = None
            content_type = None
            if courseId:
                object_id = courseId
                content_type_obj = get_content_type(Course)
                if content_type_obj:
                    content_type = content_type_obj.id
            learner_email_task.course_enrollment(course, event_type=event_type, object_id=object_id, content_type=content_type)

        messages.success(request, "Student Enrolled Successfully.")
        return HttpResponseRedirect('/yoshimitsujpinfy/admin_iffco/')

