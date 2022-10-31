using Business.Interfaces;
using Dtos.ProcessDtos;
using Microsoft.AspNetCore.Authorization;
using Microsoft.AspNetCore.Mvc;
using UI.Extensions;

namespace UI.Controllers {


    [AutoValidateAntiforgeryToken]
    [Authorize(Roles = "Member")]
    public class ProcessController : Controller {

        private readonly IProcessService _processService;

        public ProcessController(IProcessService processService) {
            _processService = processService;
        }


        [HttpGet]
        public async Task<IActionResult> Index(long id) {
            var data = await _processService.GetParameterRelatedById(id);
            return View(data.Data);
        }


        [HttpPost]
        public async Task<IActionResult> Create(ProcessCreateDto model) {
            var response = await _processService.Create(model);
            return RedirectToAction("Index", "Process", new { @id = model.SessionId });
        }


        public async Task<IActionResult> Remove(long id, long sessionId) {
            var response = await _processService.Remove(id);
            return this.ResponseRedirectToAction(response, "Index", new { id = sessionId });
        }


    }
}