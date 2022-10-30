using Business.Interfaces;
using DataAccess.UnitOfWork;
using Dtos.ProcessDtos;
using Dtos.StreamDtos;
using Entities.Concrete;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.Rendering;
using Microsoft.EntityFrameworkCore;

namespace UI.ViewComponents {
    public class StreamSelectListByPlayerFilter : ViewComponent {

        private readonly IGenericService _genericService;
        private readonly IUnitOfWork _unitOfWork;

        public StreamSelectListByPlayerFilter(IGenericService genericService, IUnitOfWork unitOfWork) {
            _genericService = genericService;
            _unitOfWork = unitOfWork;
        }

        public async Task<IViewComponentResult> InvokeAsync(long playerId, long sessionId) {
            var query = _unitOfWork.GetRepository<Process>().GetQuery().AsNoTracking();
            var isUsedValue = await query.Include(x => x.ProcessParameter).Where(x => x.SessionId == sessionId).Select(x => x.ProcessParameter != null ? x.ProcessParameter.StreamId : 0).ToListAsync();

            var results = await _genericService.GetListByFilter<StreamListDto, Entities.Concrete.Stream>(x => x.PlayerId == playerId);

            foreach (var id in isUsedValue) {

                var item = results.Data.Where(x=>x.Id == id).SingleOrDefault();
                if (item!=null){
                    results.Data.Remove(item);
                }
                
            }

            var data = new SelectList(results.Data, "Id", "Name", "StreamId");
            return View(data);
        }

    }
}